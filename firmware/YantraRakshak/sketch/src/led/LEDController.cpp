#include "LEDController.h"

#include "../config/Config.h"

LEDController::LEDController()
    : currentMode_(Mode::kHealthy), blinkOn_(true), lastBlinkToggleMs_(0) {}

void LEDController::begin() {
    pinMode(LedConfig::kPinRed, OUTPUT);
    pinMode(LedConfig::kPinGreen, OUTPUT);
    pinMode(LedConfig::kPinBlue, OUTPUT);
    render();
}

void LEDController::setMode(Mode mode) {
    if (mode == currentMode_) {
        return;
    }

    currentMode_ = mode;
    blinkOn_ = true;
    lastBlinkToggleMs_ = millis();
    render();
}

void LEDController::update() {
    if (currentMode_ != Mode::kCommFailure) {
        return;
    }

    const uint32_t now = millis();
    if ((now - lastBlinkToggleMs_) >= LedConfig::kBlinkIntervalMs) {
        lastBlinkToggleMs_ = now;
        blinkOn_ = !blinkOn_;
        render();
    }
}

void LEDController::render() {
    switch (currentMode_) {
        case Mode::kHealthy:
            applyColor(0, LedConfig::kBrightness, 0);
            break;
        case Mode::kWarning:
            applyColor(LedConfig::kBrightness, LedConfig::kBrightness, 0);
            break;
        case Mode::kCritical:
            applyColor(LedConfig::kBrightness, 0, 0);
            break;
        case Mode::kCommFailure:
            applyColor(blinkOn_ ? LedConfig::kBrightness : 0, 0, 0);
            break;
    }
}

void LEDController::applyColor(uint8_t red, uint8_t green, uint8_t blue) {
    analogWrite(LedConfig::kPinRed, red);
    analogWrite(LedConfig::kPinGreen, green);
    analogWrite(LedConfig::kPinBlue, blue);
}
