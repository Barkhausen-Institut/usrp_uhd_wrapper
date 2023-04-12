#pragma once
#include <complex>
#include <vector>

namespace bi {
const int SAMPLES_PER_BUFFER = 2000;
const int SAMPLES_PER_CYCLE = 2;
typedef std::complex<float> sample;
typedef std::vector<sample> samples_vec;
typedef std::vector<samples_vec> MimoSignal;

struct RfConfig {
    RfConfig() {}
    RfConfig(const float _txGain, const float _rxGain,
             const float _txCarrierFrequency, const float _rxCarrierFrequency,
             const float _txAnalogFilterBw, const float _rxAnalogFilterBw,
             const float _txSamplingRate, const float _rxSamplingRate,
             const int _noTxAntennas, const int _noRxAntennas)
        : txGain(_txGain),
          rxGain(_rxGain),
          txCarrierFrequency(_txCarrierFrequency),
          rxCarrierFrequency(_rxCarrierFrequency),
          txAnalogFilterBw(_txAnalogFilterBw),
          rxAnalogFilterBw(_rxAnalogFilterBw),
          txSamplingRate(_txSamplingRate),
          rxSamplingRate(_rxSamplingRate),
          noTxAntennas(_noTxAntennas),
          noRxAntennas(_noRxAntennas) {}
    float txGain, rxGain;
    float txCarrierFrequency, rxCarrierFrequency;
    float txAnalogFilterBw, rxAnalogFilterBw;
    float txSamplingRate, rxSamplingRate;
    int noTxAntennas, noRxAntennas;
};

struct TxStreamingConfig {
    TxStreamingConfig() {}
    TxStreamingConfig(const MimoSignal& _samples, const double _sendTimeOffset)
        : samples(_samples), sendTimeOffset(_sendTimeOffset) {}
    MimoSignal samples;
    double sendTimeOffset;
};

struct RxStreamingConfig {
    RxStreamingConfig() {}
    RxStreamingConfig(const unsigned int _noSamples,
                      const double _receiveTimeOffset)
        : noSamples(_noSamples), receiveTimeOffset(_receiveTimeOffset) {}
    unsigned int noSamples;
    double receiveTimeOffset;
};

bool operator==(const RfConfig& a, const RfConfig& b);
bool operator!=(const RfConfig& a, const RfConfig& b);
bool operator==(const TxStreamingConfig& a, const TxStreamingConfig& b);
bool operator==(const RxStreamingConfig& a, const RxStreamingConfig& b);

size_t calcNoPackages(const size_t noSamples, const size_t spb);
size_t calcNoSamplesLastBuffer(const size_t noSamples, const size_t spb);
void assertSamplingRate(const double actualSamplingRate,
                        const double masterClockRate,
                        bool supportsDecimation);

void assertValidTxStreamingConfig(const TxStreamingConfig& prevConfig,
                                  const TxStreamingConfig& newConfig,
                                  const double guardOffset, const double fs);

void assertValidRxStreamingConfig(const RxStreamingConfig& prevConfig,
                                  const RxStreamingConfig& newConfig,
                                  const double guardOffset, const double fs);

void assertValidTxSignal(const MimoSignal& antSamples, const size_t maxSamples,
                         const size_t noTxAntennas);

void assertValidRfConfig(const RfConfig& conf);

std::ostream& operator<<(std::ostream& os, const RfConfig& conf);
}  // namespace bi
