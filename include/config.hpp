#pragma once
#include <complex>
#include <vector>

namespace bi {
const int SAMPLES_PER_BUFFER = 2000;
typedef std::complex<float> sample;
typedef std::vector<sample> samples_vec;

struct RfConfig {
    RfConfig() {}
    RfConfig(const std::vector<float>& _txGain,
             const std::vector<float>& _rxGain,
             const std::vector<float>& _txCarrierFrequency,
             const std::vector<float>& _rxCarrierFrequency,
             const float _txAnalogFilterBw, const float _rxAnalogFilterBw,
             const float _txSamplingRate, const float _rxSamplingRate)
        : txGain(_txGain),
          rxGain(_rxGain),
          txCarrierFrequency(_txCarrierFrequency),
          rxCarrierFrequency(_rxCarrierFrequency),
          txAnalogFilterBw(_txAnalogFilterBw),
          rxAnalogFilterBw(_rxAnalogFilterBw),
          txSamplingRate(_txSamplingRate),
          rxSamplingRate(_rxSamplingRate) {}
    std::vector<float> txGain, rxGain;
    std::vector<float> txCarrierFrequency, rxCarrierFrequency;
    float txAnalogFilterBw, rxAnalogFilterBw;
    float txSamplingRate, rxSamplingRate;
};

struct TxStreamingConfig {
    TxStreamingConfig() {}
    TxStreamingConfig(const std::vector<samples_vec>& _samples,
                      const float _sendTimeOffset)
        : samples(_samples), sendTimeOffset(_sendTimeOffset) {}
    std::vector<samples_vec> samples;
    float sendTimeOffset;
};

struct RxStreamingConfig {
    RxStreamingConfig() {}
    RxStreamingConfig(const unsigned int _noSamples,
                      const float _receiveTimeOffset)
        : noSamples(_noSamples), receiveTimeOffset(_receiveTimeOffset) {}
    unsigned int noSamples;
    float receiveTimeOffset;
};

// oerpators are overloaded for testing purposes
bool operator==(const RfConfig& a, const RfConfig& b);
bool operator==(const TxStreamingConfig& a, const TxStreamingConfig& b);
bool operator==(const RxStreamingConfig& a, const RxStreamingConfig& b);

size_t calcNoPackages(const size_t noSamples, const size_t spb);
size_t calcNoSamplesLastBuffer(const size_t noSamples, const size_t spb);
void assertSamplingRate(const double actualSamplingRate,
                        const double masterClockRate);

}  // namespace bi
