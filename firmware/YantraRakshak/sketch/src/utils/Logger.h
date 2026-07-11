#ifndef YANTRA_RAKSHAK_LOGGER_H
#define YANTRA_RAKSHAK_LOGGER_H

#include <Arduino.h>

// Severity levels, ordered so that comparisons (level < kMinimumLevel) can be
// used directly to decide whether a message should be printed.
enum class LogLevel : uint8_t {
    kInfo  = 0,
    kWarn  = 1,
    kError = 2
};

// Centralized serial logging so every module reports diagnostics in a single
// consistent format instead of scattering raw Serial.print calls.
class Logger {
public:
    // Initializes the serial port used for log output. Must be called once
    // from setup() before any other Logger method is used.
    static void begin(unsigned long baudRate);

    static void info(const char* tag, const char* message);
    static void warn(const char* tag, const char* message);
    static void error(const char* tag, const char* message);

private:
    // Minimum severity that is actually printed. Raise to kError for a
    // production flash to reduce serial I/O overhead in the main loop.
    static constexpr LogLevel kMinimumLevel = LogLevel::kInfo;

    static void log(LogLevel level, const char* tag, const char* message);
    static const char* levelToString(LogLevel level);
};

#endif // YANTRA_RAKSHAK_LOGGER_H
