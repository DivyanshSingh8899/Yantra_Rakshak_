#ifndef YANTRA_RAKSHAK_CIRCULAR_BUFFER_H
#define YANTRA_RAKSHAK_CIRCULAR_BUFFER_H

#include <Arduino.h>

// Fixed-capacity ring buffer shared by both sensor streams (vibration and
// audio). The producer (a sensor driver, via SensorManager) calls push() on
// every sample; the consumer (SignalProcessor) polls isWindowReady() /
// consumeWindow() once enough new samples have accumulated.
//
// When full, push() overwrites the oldest entry rather than blocking --
// real-time freshness matters more than completeness for anomaly detection,
// so a slow consumer never stalls the sampling loop.
template <typename T, size_t Capacity>
class CircularBuffer {
public:
    static_assert(Capacity > 0, "CircularBuffer capacity must be greater than zero");

    CircularBuffer()
        : writeIndex_(0), count_(0), newSamplesSinceWindow_(0) {}

    // Stores one sample, overwriting the oldest entry once the buffer is
    // full. O(1); safe to call from a tight sampling loop.
    void push(const T& sample) {
        buffer_[writeIndex_] = sample;
        writeIndex_ = (writeIndex_ + 1) % Capacity;

        if (count_ < Capacity) {
            count_++;
        }

        if (newSamplesSinceWindow_ < Capacity) {
            newSamplesSinceWindow_++;
        }
    }

    // Total valid samples currently held (saturates at Capacity).
    size_t size() const {
        return count_;
    }

    size_t capacity() const {
        return Capacity;
    }

    bool isFull() const {
        return count_ == Capacity;
    }

    // True once the buffer holds at least windowSize samples in total AND
    // at least windowSize new samples have arrived since the last
    // consumeWindow() call.
    bool isWindowReady(size_t windowSize) const {
        return count_ >= windowSize && newSamplesSinceWindow_ >= windowSize;
    }

    // Copies the most recent windowSize samples, oldest-to-newest, into
    // destination (caller-owned, must hold at least windowSize elements).
    // Returns false without modifying destination if fewer than windowSize
    // samples are currently held. On success, windowSize is deducted from
    // the new-sample counter so any leftover samples beyond the window
    // still count toward triggering the next one.
    bool consumeWindow(T* destination, size_t windowSize) {
        if (destination == nullptr || count_ < windowSize) {
            return false;
        }

        for (size_t i = 0; i < windowSize; i++) {
            const size_t sourceIndex = (writeIndex_ + (2 * Capacity) - windowSize + i) % Capacity;
            destination[i] = buffer_[sourceIndex];
        }

        newSamplesSinceWindow_ -= (newSamplesSinceWindow_ >= windowSize) ? windowSize : newSamplesSinceWindow_;

        return true;
    }

private:
    T buffer_[Capacity];
    size_t writeIndex_;
    size_t count_;
    size_t newSamplesSinceWindow_;
};

#endif // YANTRA_RAKSHAK_CIRCULAR_BUFFER_H
