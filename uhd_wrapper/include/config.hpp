#pragma once
#include <complex>
#include <vector>

namespace bi {
const int SAMPLES_PER_BUFFER = 2000;
typedef std::complex<float> sample;
typedef std::vector<sample> samples_vec;
typedef std::vector<samples_vec> MimoSignal;

struct RfConfig {
    RfConfig() {}
    RfConfig(const float _txGain, const float _rxGain,
             const float _txCarrierFrequency, const float _rxCarrierFrequency,
             const float _txAnalogFilterBw, const float _rxAnalogFilterBw,
             const float _txSamplingRate, const float _rxSamplingRate,
             const int _noTxStreams, const int _noRxStreams)
        : txGain(_txGain),
          rxGain(_rxGain),
          txCarrierFrequency(_txCarrierFrequency),
          rxCarrierFrequency(_rxCarrierFrequency),
          txAnalogFilterBw(_txAnalogFilterBw),
          rxAnalogFilterBw(_rxAnalogFilterBw),
          txSamplingRate(_txSamplingRate),
          rxSamplingRate(_rxSamplingRate),
          noTxStreams(_noTxStreams),
          noRxStreams(_noRxStreams) {}
    float txGain, rxGain;
    float txCarrierFrequency, rxCarrierFrequency;
    float txAnalogFilterBw, rxAnalogFilterBw;
    float txSamplingRate, rxSamplingRate;
    int noTxStreams, noRxStreams;
    std::vector<int> txAntennaMapping;
    std::vector<int> rxAntennaMapping;
};

struct TxStreamingConfig {
    TxStreamingConfig() {}
    TxStreamingConfig(const MimoSignal& _samples,
                      const double _sendTimeOffset,
                      const int _repetitions)
        : samples(_samples), sendTimeOffset(_sendTimeOffset), repetitions(_repetitions) {}
    MimoSignal samples;
    double sendTimeOffset;
    int repetitions;

    void alignToWordSize();
};

struct RxStreamingConfig {
    RxStreamingConfig() {}
    RxStreamingConfig(const unsigned int _noSamples,
                      const double _receiveTimeOffset,
                      const std::string& _antennaPort = "",
                      const unsigned int _numRepetitions = 1,
                      const unsigned int _repetitionPeriod = 0)
        : noSamples(_noSamples),
          receiveTimeOffset(_receiveTimeOffset),
          numRepetitions(_numRepetitions),
          repetitionPeriod(_repetitionPeriod),
          antennaPort(_antennaPort) {}
    unsigned int noSamples;
    double receiveTimeOffset;
    unsigned int numRepetitions = 1;
    unsigned int repetitionPeriod = 0;
    std::string antennaPort;

    size_t wordAlignedNoSamples() const;
    size_t totalWordAlignedSamples() const;
    size_t totalSamples() const;
};

size_t nextMultipleOfWordSize(size_t count);
void extendToWordSize(MimoSignal& samples);
void shortenSignal(MimoSignal& samples, size_t length);

bool operator==(const RfConfig& a, const RfConfig& b);
bool operator!=(const RfConfig& a, const RfConfig& b);
bool operator==(const TxStreamingConfig& a, const TxStreamingConfig& b);
bool operator==(const RxStreamingConfig& a, const RxStreamingConfig& b);

size_t calcNoPackages(const size_t noSamples, const size_t spb);
size_t calcNoSamplesLastBuffer(const size_t noSamples, const size_t spb);
void assertSamplingRate(const double actualSamplingRate,
                        const double masterClockRate,
                        bool supportsDecimation);

void assertValidTxStreamingConfig(const TxStreamingConfig* prevConfig,
                                  const TxStreamingConfig& newConfig,
                                  const double guardOffset, const double fs);

void assertValidRxStreamingConfig(const RxStreamingConfig* prevConfig,
                                  const RxStreamingConfig& newConfig,
                                  const double guardOffset, const double fs);

void assertValidTxSignal(const MimoSignal& antSamples, const size_t maxSamples,
                         const size_t noTxAntennas);

void assertValidRfConfig(const RfConfig& conf);

std::ostream& operator<<(std::ostream& os, const RfConfig& conf);
}  // namespace bi
