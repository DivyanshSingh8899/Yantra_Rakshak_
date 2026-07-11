#include "Logger.h"

void Logger::begin(unsigned long baudRate) {
    Serial.begin(baudRate);

    // Give a host terminal a brief window to attach without blocking boot
    // indefinitely when the device is running unattended in the field.
    const uint32_t startWaitMs = millis();
    while (!Serial && (millis() - startWaitMs) < 3000) {
        // Intentionally empty: waiting for the serial connection to settle.
    }
}

void Logger::info(const char* tag, const char* message) {
    log(LogLevel::kInfo, tag, message);
}

void Logger::warn(const char* tag, const char* message) {
    log(LogLevel::kWarn, tag, message);
}

void Logger::error(const char* tag, const char* message) {
    log(LogLevel::kError, tag, message);
}

void Logger::log(LogLevel level, const char* tag, const char* message) {
    if (level < kMinimumLevel) {
        return;
    }

    Serial.print('[');
    Serial.print(millis());
    Serial.print("ms][");
    Serial.print(levelToString(level));
    Serial.print("][");
    Serial.print(tag);
    Serial.print("] ");
    Serial.println(message);
}

const char* Logger::levelToString(LogLevel level) {
    switch (level) {
        case LogLevel::kInfo:  return "INFO";
        case LogLevel::kWarn:  return "WARN";
        case LogLevel::kError: return "ERROR";
        default:               return "UNKNOWN";
    }
}
