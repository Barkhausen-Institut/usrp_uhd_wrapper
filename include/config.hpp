#pragma once
#include <complex>
#include <vector>

namespace bi {
typedef std::complex<float> sample;
typedef std::vector<sample> package;

struct RfConfig {
    int txGain, rxGain;
    int txCarrierFrequency, rxCarrierFrequency;
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
}  // namespace bi
