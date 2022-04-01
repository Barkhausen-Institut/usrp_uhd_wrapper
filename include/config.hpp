#pragma once
#include <complex>
#include <vector>

namespace bi {
const int SAMPLES_PER_BUFFER = 2000;
typedef std::complex<float> sample;
typedef std::vector<sample> samples_vec;

struct RfConfig {
    std::vector<float> txGain, rxGain;
    std::vector<float> txCarrierFrequency, rxCarrierFrequency;
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

size_t calcNoPackages(const size_t noSamples, const size_t spb);
size_t calcNoSamplesLastBuffer(const size_t noSamples, const size_t spb);

}  // namespace bi
