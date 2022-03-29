#pragma once
#include <complex>
#include <vector>

namespace bi {
const int SAMPLES_PER_BUFFER = 2000;
typedef std::complex<float> sample;
typedef std::vector<sample> samples_vec;

struct RfConfig {
    int txGain, rxGain;
    float txCarrierFrequency, rxCarrierFrequency;
    float txAnalogFilterBw, rxAnalogFilterBw;
    float txSamplingRate, rxSamplingRate;
};

struct TxStreamingConfig {
    std::vector<samples_vec> samples;
    float sendTimeOffset;
};

struct RxStreamingConfig {
    unsigned int noSamples;
    float receiveTimeOffset;
};
}  // namespace bi
