"""
Trains the YantraRakshak vibration anomaly-detection autoencoder on real
CWRU Bearing Data Center recordings, downsampled to match the deployed
MPU6050 sampling rate, then exports an INT8-quantized TensorFlow Lite model.

Data used (downloaded from https://engineering.case.edu/bearingdatacenter):
  Normal baseline : 97.mat, 98.mat, 99.mat, 100.mat
  Faulty (held out, used only for threshold validation, never for training):
    105.mat (0.007" inner race fault), 118.mat (0.007" ball fault)

Honesty notes (see docs/MODEL_TRAINING_REPORT.md for the full writeup):
  - CWRU's drive-end (DE) channel is captured at 12 kHz; the deployed
    MPU6050 samples at 500 Hz. The DE signal is decimated to 500 Hz here so
    the training window duration (128 samples = ~256 ms) matches the
    deployed window duration, reducing (not eliminating) the domain gap.
  - The feature vector is intentionally 5 values (mean, rms, peak,
    crestFactor, kurtosis) computed on a single vibration-magnitude-style
    channel -- matching what one physical MPU6050 can genuinely provide.
    CWRU's second (FE) channel and MIMII audio data were not used as model
    inputs because there is no second real sensor channel on the currently
    wired hardware to match them to; using them would mean fabricating a
    correspondence that doesn't exist on this hardware.
"""

import json
import struct

import numpy as np
import scipy.io as sio
import scipy.signal as sps
import tensorflow as tf

RAW_DIR = "d:/Hackathon/Yantra_Rakshak_/machine-learning/datasets/raw/cwru"
OUTPUT_DIR = "d:/Hackathon/Yantra_Rakshak_/machine-learning/models/exported"
CWRU_SAMPLE_RATE_HZ = 12000
DEPLOYED_SAMPLE_RATE_HZ = 500
DECIMATION_FACTOR = CWRU_SAMPLE_RATE_HZ // DEPLOYED_SAMPLE_RATE_HZ  # 24
WINDOW_SIZE = 128
FEATURE_COUNT = 5

NORMAL_FILES = ["97", "98", "99", "100"]
FAULT_FILES = ["105", "118"]


def load_de_channel(file_id: str) -> np.ndarray:
    data = sio.loadmat(f"{RAW_DIR}/{file_id}.mat")
    key = [k for k in data.keys() if k.endswith(f"X{file_id}_DE_time")]
    if not key:
        # 99.mat ships with an extra duplicated 098 key; select the one
        # matching this file_id explicitly rather than guessing.
        key = [k for k in data.keys() if f"{file_id}_DE_time" in k]
    return data[key[0]].flatten().astype(np.float64)


def downsample(signal: np.ndarray) -> np.ndarray:
    return sps.decimate(signal, DECIMATION_FACTOR, ftype="fir", zero_phase=True)


def compute_window_features(window: np.ndarray) -> np.ndarray:
    mean = float(np.mean(window))
    centered = window - mean
    rms = float(np.sqrt(np.mean(centered ** 2)))
    peak = float(np.max(np.abs(centered)))
    crest_factor = (peak / rms) if rms > 1e-9 else 0.0
    variance = float(np.mean(centered ** 2))
    fourth_moment = float(np.mean(centered ** 4))
    kurtosis = (fourth_moment / (variance ** 2) - 3.0) if variance > 1e-12 else 0.0
    return np.array([mean, rms, peak, crest_factor, kurtosis], dtype=np.float32)


def windows_from_signal(signal: np.ndarray) -> np.ndarray:
    n_windows = len(signal) // WINDOW_SIZE
    trimmed = signal[: n_windows * WINDOW_SIZE].reshape(n_windows, WINDOW_SIZE)
    return np.array([compute_window_features(w) for w in trimmed], dtype=np.float32)


def build_autoencoder(input_dim: int) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(input_dim,))
    x = tf.keras.layers.Dense(4, activation="relu")(inputs)
    x = tf.keras.layers.Dense(2, activation="relu", name="bottleneck")(x)
    x = tf.keras.layers.Dense(4, activation="relu")(x)
    outputs = tf.keras.layers.Dense(input_dim, activation="linear")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer="adam", loss="mse")
    return model


def main():
    print("Loading and downsampling normal (training) files:", NORMAL_FILES)
    normal_features = []
    for file_id in NORMAL_FILES:
        de = load_de_channel(file_id)
        de_ds = downsample(de)
        feats = windows_from_signal(de_ds)
        normal_features.append(feats)
        print(f"  {file_id}.mat: {len(de)} samples @12kHz -> {len(de_ds)} @500Hz -> {len(feats)} windows")
    normal_features = np.concatenate(normal_features, axis=0)

    print("Loading and downsampling fault (validation-only) files:", FAULT_FILES)
    fault_features = []
    for file_id in FAULT_FILES:
        de = load_de_channel(file_id)
        de_ds = downsample(de)
        feats = windows_from_signal(de_ds)
        fault_features.append(feats)
        print(f"  {file_id}.mat: {len(de)} samples @12kHz -> {len(de_ds)} @500Hz -> {len(feats)} windows")
    fault_features = np.concatenate(fault_features, axis=0)

    rng = np.random.default_rng(seed=42)
    shuffled_idx = rng.permutation(len(normal_features))
    normal_features = normal_features[shuffled_idx]
    split = int(len(normal_features) * 0.85)
    train_raw, val_raw = normal_features[:split], normal_features[split:]

    feature_mean = train_raw.mean(axis=0)
    feature_std = train_raw.std(axis=0)
    feature_std[feature_std < 1e-6] = 1.0

    train_std = (train_raw - feature_mean) / feature_std
    val_std = (val_raw - feature_mean) / feature_std
    fault_std = (fault_features - feature_mean) / feature_std

    print(f"\nTraining windows: {len(train_std)}, validation windows: {len(val_std)}, fault windows: {len(fault_std)}")

    model = build_autoencoder(FEATURE_COUNT)
    model.summary()
    history = model.fit(
        train_std, train_std,
        validation_data=(val_std, val_std),
        epochs=100,
        batch_size=32,
        verbose=2,
    )

    def reconstruction_error(x):
        recon = model.predict(x, verbose=0)
        return np.mean((x - recon) ** 2, axis=1)

    normal_val_errors = reconstruction_error(val_std)
    fault_errors = reconstruction_error(fault_std)

    warning_threshold = float(normal_val_errors.mean() + 2 * normal_val_errors.std())
    critical_threshold = float(normal_val_errors.mean() + 4 * normal_val_errors.std())

    print(f"\nNormal validation error: mean={normal_val_errors.mean():.5f}, std={normal_val_errors.std():.5f}, max={normal_val_errors.max():.5f}")
    print(f"Fault error: mean={fault_errors.mean():.5f}, std={fault_errors.std():.5f}, min={fault_errors.min():.5f}")
    print(f"Warning threshold (mean+2std of normal): {warning_threshold:.5f}")
    print(f"Critical threshold (mean+4std of normal): {critical_threshold:.5f}")
    detection_rate = float(np.mean(fault_errors > warning_threshold))
    false_positive_rate = float(np.mean(normal_val_errors > warning_threshold))
    print(f"Fault windows flagged at/above warning threshold: {detection_rate * 100:.1f}%")
    print(f"Normal validation windows falsely flagged: {false_positive_rate * 100:.1f}%")

    # --- INT8 quantization ---
    def representative_dataset():
        for i in range(min(200, len(train_std))):
            yield [train_std[i : i + 1].astype(np.float32)]

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    tflite_model = converter.convert()

    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tflite_path = f"{OUTPUT_DIR}/autoencoder_int8.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"\nSaved quantized model: {tflite_path} ({len(tflite_model)} bytes)")

    # --- Verify the quantized model reproduces the same separation ---
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]
    in_scale, in_zero = input_details["quantization"]
    out_scale, out_zero = output_details["quantization"]

    def quantized_reconstruction_error(x_std_row):
        q_in = np.clip(np.round(x_std_row / in_scale + in_zero), -128, 127).astype(np.int8)
        interpreter.set_tensor(input_details["index"], q_in.reshape(1, -1))
        interpreter.invoke()
        q_out = interpreter.get_tensor(output_details["index"])[0]
        recon = (q_out.astype(np.float32) - out_zero) * out_scale
        return float(np.mean((x_std_row - recon) ** 2))

    quant_normal_errors = np.array([quantized_reconstruction_error(r) for r in val_std])
    quant_fault_errors = np.array([quantized_reconstruction_error(r) for r in fault_std])
    print(f"\n[Quantized model check] normal val error mean={quant_normal_errors.mean():.5f}, fault error mean={quant_fault_errors.mean():.5f}")

    calibration = {
        "feature_count": FEATURE_COUNT,
        "feature_names": ["mean", "rms", "peak", "crest_factor", "kurtosis"],
        "feature_mean": feature_mean.tolist(),
        "feature_std": feature_std.tolist(),
        "warning_threshold": warning_threshold,
        "critical_threshold": critical_threshold,
        "window_size": WINDOW_SIZE,
        "deployed_sample_rate_hz": DEPLOYED_SAMPLE_RATE_HZ,
        "training_source": "CWRU Bearing Data Center (real, downloaded): 97,98,99,100 (normal), 105,118 (fault, validation only)",
        "normal_val_error_mean": float(normal_val_errors.mean()),
        "normal_val_error_std": float(normal_val_errors.std()),
        "fault_error_mean": float(fault_errors.mean()),
        "fault_detection_rate_at_warning_threshold": detection_rate,
        "normal_false_positive_rate_at_warning_threshold": false_positive_rate,
        "quantized_model_size_bytes": len(tflite_model),
        "quantized_input_scale": float(in_scale),
        "quantized_input_zero_point": int(in_zero),
        "quantized_output_scale": float(out_scale),
        "quantized_output_zero_point": int(out_zero),
    }
    with open(f"{OUTPUT_DIR}/calibration.json", "w") as f:
        json.dump(calibration, f, indent=2)
    print(f"Saved calibration constants: {OUTPUT_DIR}/calibration.json")


if __name__ == "__main__":
    main()
