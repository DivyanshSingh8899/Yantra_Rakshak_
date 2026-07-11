# TinyML Model Training Report

Real training run, real data, real results. This replaces the earlier design-only TinyML pipeline document with what was actually executed. Reproduce by running `machine-learning/training/train_autoencoder.py` (requires `pip install tensorflow numpy scipy` — see `machine-learning/requirements.txt`).

## 1. Data Sources

### CWRU Bearing Data Center (used)
Downloaded directly from https://engineering.case.edu/bearingdatacenter (12 kHz drive-end recordings):

| File | Condition | Role |
|---|---|---|
| 97.mat, 98.mat, 99.mat, 100.mat | Normal baseline (0-3 HP load) | Training + validation (autoencoder trained on normal only) |
| 105.mat | 0.007" inner race fault | Held out entirely from training; used only to validate detection/threshold |
| 118.mat | 0.007" ball fault | Held out entirely from training; used only to validate detection/threshold |

Total real data downloaded: ~40 MB across 6 `.mat` files.

### MIMII Dataset (not used — documented, not silently dropped)
Every individual file in the MIMII Zenodo record (https://zenodo.org/records/3384388) is **6.9 GB or larger** (smallest: `6_dB_valve.zip`); the full dataset is 100.2 GB. Downloading any single file was not feasible within this session's practical time/bandwidth constraints. Rather than fabricate synthetic audio and present it as real MIMII-derived training data, the audio/microphone branch was dropped from this model entirely — which also happens to match the hardware finding that the INMP441's I2S interface isn't wireable on real UNO Q hardware anyway (see `docs/ARDUINO_UNO_Q_API_VERIFICATION.md`). Audio can be reintroduced later via a real on-site recording campaign (Phase 4 of the original roadmap) once a working microphone input path (analog sensor or Qualcomm-side JMISC audio) is chosen.

## 2. Feature Design (reduced from 32 to 5, and why)

The original design's 32-feature vector assumed 3-axis accelerometer + 3-axis gyroscope + audio, fused. Real available data only supports:

- CWRU provides **single-axis** accelerometer channels (DE = drive-end, FE = fan-end) — not the 3-axis + gyro + audio combination the original design assumed.
- Our actual hardware has **one** MPU6050 (one mounting point). CWRU's DE channel was mapped to the MPU6050's combined 3-axis acceleration **magnitude** signal — both represent "overall vibration energy at one measurement point," a legitimate, explainable correspondence. FE-channel data was downloaded and is available in `machine-learning/datasets/raw/cwru/` for a future second-sensor deployment, but was not used as a model input since there's no second real sensor on the current hardware to match it to.
- Gyroscope and audio features were dropped entirely rather than filled with fabricated/duplicated values, since CWRU has no gyroscope or audio channels at all.

**Final feature vector (5 values)**, computed per 128-sample window on the acceleration-magnitude signal: `mean, rms, peak, crest_factor, kurtosis`. Kurtosis was added (not in the original 4-stat design) because it is the standard, cheap, FFT-free statistic for detecting the impulsive shock content characteristic of bearing faults — directly relevant given the training data is bearing-fault recordings.

## 3. Sample-Rate Domain Gap (real limitation, disclosed)

CWRU's DE channel is sampled at 12 kHz; the deployed MPU6050 samples at 500 Hz. To reduce (not eliminate) this gap, the DE signal was **decimated 24x to 500 Hz** (`scipy.signal.decimate`, FIR anti-aliasing, zero-phase) before windowing, so the training window duration (128 samples ≈ 256 ms) matches the deployed window duration. This is a legitimate DSP practice, but a real domain gap remains: the statistical *shape* features used here (mean/rms/peak/crest-factor/kurtosis) are relatively robust to this kind of rate change, but the exact calibrated thresholds below should be treated as a bootstrap, not a final production calibration — recalibrate against real MPU6050 recordings from the actual target machine once available (Phase 4 of the roadmap), the same way any vibration-monitoring deployment would.

## 4. Model Architecture (as actually trained)

Dense autoencoder, Keras/TensorFlow 2.21.0:

```
Input(5) -> Dense(4, relu) -> Dense(2, relu, "bottleneck") -> Dense(4, relu) -> Dense(5, linear)
```
71 trainable parameters. Trained 100 epochs, Adam optimizer, MSE loss, batch size 32, on 468 training windows (85% split) with 83 held out for validation — both drawn only from the normal-baseline files.

## 5. Results (actual numbers from this run)

| Metric | Value |
|---|---|
| Normal validation reconstruction error | mean 0.640, std 0.569 |
| Fault (105+118, held out) reconstruction error | mean 17.65, std 2.74 |
| Warning threshold (mean + 2·std of normal) | 1.777 |
| Critical threshold (mean + 4·std of normal) | 2.914 |
| **Fault windows flagged at/above warning threshold** | **100%** (78/78) |
| Normal validation windows falsely flagged | 7.2% (6/83) |
| Quantized (INT8) model normal error mean | 0.640 (matches float model) |
| Quantized (INT8) model fault error mean | 17.67 (matches float model) |
| Quantized model size | 3,264 bytes |

The ~27x separation between normal and fault reconstruction error, and 100% detection at the chosen threshold, indicate the autoencoder learned a genuine, strong signal from real bearing-fault data — not a fitting artifact (faults were never seen during training). The 7.2% false-positive rate on normal validation windows is a real tradeoff of the mean+2σ threshold choice; tightening it (e.g., mean+2.5σ) would trade some detection sensitivity for fewer false alarms, and should be tuned against real deployed-hardware data once collected.

## 6. Quantization

Full-integer post-training quantization (`tf.lite.TFLiteConverter`, `TFLITE_BUILTINS_INT8`, both input and output int8), calibrated against 200 representative standardized training windows. Verified directly (Section 5) that the quantized model reproduces the same normal/fault error separation as the float model — quantization did not degrade discriminative power for this model.

Quantization parameters (from the actual converted model):

| Parameter | Value |
|---|---|
| Input scale / zero point | 0.024671 / -2 |
| Output scale / zero point | 0.014544 / -85 |

## 7. Generated Artifacts

| File | Contents |
|---|---|
| `machine-learning/models/exported/autoencoder_int8.tflite` | The real quantized model (3,264 bytes) |
| `machine-learning/models/exported/calibration.json` | Full calibration constants (feature mean/std, thresholds, quantization params, evaluation metrics) |
| `firmware/YantraRakshak/sketch/src/ml/model_data.cpp` / `.h` | The same model bytes as a C array (`g_model[]`, `g_model_len`) for the experimental on-MCU inference path |
| `firmware/YantraRakshak/python/model/autoencoder_int8.tflite` | The same model, loaded directly by the recommended Python-side inference path |
| `firmware/YantraRakshak/sketch/src/signal/SignalProcessor.cpp` | Feature extraction + standardization using the real trained mean/std constants above |
| `firmware/YantraRakshak/sketch/src/config/Config.h` | Real trained warning/critical thresholds |

## 8. Honest Limitations Going Into Hardware Testing

1. **Domain gap**: trained on lab-grade CWRU accelerometer data (decimated to match deployment rate), not on data from the actual deployed MPU6050. Treat current thresholds as a bootstrap calibration.
2. **No audio branch**: dropped due to both real dataset-size infeasibility (MIMII) and a real hardware constraint (I2S not exposed on UNO Q). Not fabricated as a workaround.
3. **Single fault-vs-normal detector**: this model distinguishes normal vibration from anomalous vibration; it was never trained to distinguish *between* different fault types (inner race vs. ball vs. imbalance, etc.), so `python/main.py`'s fault label reports a generic "Bearing Fault Signature" rather than inventing a specific fault taxonomy the model can't actually support.
4. **On-MCU inference unverified**: the TFLM/CMSIS-NN path (`AnomalyDetector.cpp`) is provided but its buildability through Arduino's `arduino:zephyr` CLI wrapper is unconfirmed (see `docs/ARDUINO_UNO_Q_API_VERIFICATION.md`); the Python-side path is the one to rely on by default.
