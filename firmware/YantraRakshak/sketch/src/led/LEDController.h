#ifndef YANTRA_RAKSHAK_LED_CONTROLLER_H
#define YANTRA_RAKSHAK_LED_CONTROLLER_H

#include <Arduino.h>

// Owns the RGB LED's three PWM channels and translates system state into
// the defined color/blink patterns: Green = Healthy, Yellow = Warning,
// Red = Critical, Blinking Red = communication failure.
class LEDController {
public:
    enum class Mode : uint8_t { kHealthy, kWarning, kCritical, kCommFailure };

    LEDController();

    void begin();

    // Sets the current display mode. Cheap to call every loop with the
    // same mode already set (no-op beyond the blink timer check in
    // update()).
    void setMode(Mode mode);

    // Services the blink timer for kCommFailure mode. Call once per main
    // loop iteration.
    void update();

private:
    Mode currentMode_;
    bool blinkOn_;
    uint32_t lastBlinkToggleMs_;

    void render();
    void applyColor(uint8_t red, uint8_t green, uint8_t blue);
};

#endif // YANTRA_RAKSHAK_LED_CONTROLLER_H
