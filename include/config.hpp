#pragma once
#include <complex>

typedef std::complex<float> sample;
typedef std::vector<sample> package;

struct RfConfig {
    int txGain, rxGain;
    int carrierFrequency;
    int txAnalogFilterBw, rxAnalogFilterBw;
    int txSamplingRate, rxSamplingRate;
};

struct TxStreamingConfig {
    package samples;
    float sendTimeOffset;
};

struct RxStreamingConfig {
    unsigned int noSamples;
    float receiveTimeOffset;
};