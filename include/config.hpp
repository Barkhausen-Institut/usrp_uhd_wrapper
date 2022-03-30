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

inline void zeroPadSignal(const size_t spb, samples_vec& samples) {
    size_t noZeroPadding = samples.size() % spb;
    size_t noSamples = noZeroPadding + samples.size();
    samples.resize(noSamples, sample(0, 0));
}

}  // namespace bi
