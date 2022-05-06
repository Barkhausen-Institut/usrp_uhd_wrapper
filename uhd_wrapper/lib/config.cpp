#include "config.hpp"
#include "usrp_exception.hpp"

namespace bi {

bool operator==(const RfConfig& a, const RfConfig& b) {
    bool equal = true;
    equal &= a.txGain == b.txGain;
    equal &= a.rxGain == b.rxGain;
    equal &= a.txCarrierFrequency == b.txCarrierFrequency;
    equal &= a.rxCarrierFrequency == b.rxCarrierFrequency;
    equal &= a.txAnalogFilterBw == b.txAnalogFilterBw;
    equal &= a.rxAnalogFilterBw == b.rxAnalogFilterBw;
    equal &= a.txSamplingRate == b.txSamplingRate;
    equal &= a.rxSamplingRate == b.rxSamplingRate;
    return equal;
}

bool operator==(const RxStreamingConfig& a, const RxStreamingConfig& b) {
    bool equal = true;
    equal &= a.noSamples == b.noSamples;
    equal &= a.receiveTimeOffset == b.receiveTimeOffset;
    return equal;
}

bool operator==(const TxStreamingConfig& a, const TxStreamingConfig& b) {
    bool equal = true;
    equal &= a.samples == b.samples;
    equal &= a.sendTimeOffset == b.sendTimeOffset;
    return equal;
}
size_t calcNoPackages(const size_t noSamples, const size_t spb) {
    // taken from
    // https://stackoverflow.com/questions/2745074/fast-ceiling-of-an-integer-division-in-c-c
    return (noSamples + spb - 1) / spb;
}
size_t calcNoSamplesLastBuffer(const size_t noSamples, const size_t spb) {
    size_t noSamplesLastBuffer = noSamples % spb;
    if (noSamplesLastBuffer == 0) noSamplesLastBuffer = spb;
    return noSamplesLastBuffer;
}

void assertSamplingRate(const double actualSamplingRate,
                        const double masterClockRate) {
    // avoid floating inprecision issues
    if (std::fmod(masterClockRate / actualSamplingRate, 2.0) > 0.01 &&
        masterClockRate != actualSamplingRate)
        throw UsrpException("Sampling rate must be an even fraction of " +
                            std::to_string(masterClockRate));
}

void assertValidTxStreamingConfig(const TxStreamingConfig& prevConfig,
                                  const TxStreamingConfig& newConfig,
                                  const double guardOffset, const double fs) {
    double minimumRequiredOffset = prevConfig.sendTimeOffset + guardOffset +
                                   prevConfig.samples[0].size() / fs;
    if (newConfig.sendTimeOffset < minimumRequiredOffset)
        throw UsrpException(
            "Invalid TX streaming config: the offset of the new config is too "
            "small.");
}
void assertValidRxStreamingConfig(const RxStreamingConfig& prevConfig,
                                  const RxStreamingConfig& newConfig,
                                  const double guardOffset, const double fs) {
    double minimumRequiredOffset =
        prevConfig.receiveTimeOffset + guardOffset + prevConfig.noSamples / fs;
    if (newConfig.receiveTimeOffset < minimumRequiredOffset)
        throw UsrpException(
            "Invalid TX streaming config: the offset of the new config is too "
            "small.");
}
}  // namespace bi