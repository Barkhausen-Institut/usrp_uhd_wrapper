#include <iostream>
#include <algorithm>

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

bool operator!=(const RfConfig& a, const RfConfig& b) { return !(a == b); }

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

size_t nextMultipleOfWordSize(size_t count) {
    const size_t WORD_SIZE = 8;
    size_t rem = count % WORD_SIZE;

    if (rem == 0)
        return count;
    else
        return count + WORD_SIZE - rem;
}

void assertSamplingRate(const double actualSamplingRate,
                        const double masterClockRate,
                        bool supportsDecimation) {
    double ratio = actualSamplingRate / masterClockRate;
    if (!supportsDecimation) {
        if (std::abs(ratio - 1) > 0.01)
            throw UsrpException("Decimation not supported by device!");
    }


    // avoid floating inprecision issues
    double mod = std::fmod(masterClockRate / actualSamplingRate, 2.0);
    if (masterClockRate == actualSamplingRate)
        return;
    if (mod < 0.01)
        return;
    if (mod > 1.99)
        return;

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
            "Invalid RX streaming config: the offset of the new config is too "
            "small.");
}

void assertValidTxSignal(const MimoSignal& antSamples, const size_t maxSamples,
                         const size_t noTxAntennas) {
    size_t noSignals = antSamples.size();
    if (noSignals == 0) throw UsrpException("No signal provided.");
    size_t lengthSignal = antSamples[0].size();
    if (antSamples.size() != noTxAntennas)
        throw UsrpException(
            "The number of signals must match the number of tx antennas.");
    for (const auto& antSignal : antSamples) {
        if (antSignal.size() > maxSamples)
            throw UsrpException(
                "Transmitted signal length must not be larger than " +
                std::to_string(maxSamples));
        if (antSignal.size() != lengthSignal)
            throw UsrpException(
                "The antenna signals need to have the same length.");
        if (std::find_if(antSignal.begin(), antSignal.end(),
                         [](const auto& c) {
                             return std::isnan(c.real()) || std::isnan(c.imag());
                         }) != antSignal.end())
            throw UsrpException("The antenna signal contains nan values!");
    }
}

void assertValidRfConfig(const RfConfig& conf) {
    if (conf.noTxAntennas > 4 || conf.noTxAntennas < 1)
        throw UsrpException(
            "You provided " + std::to_string(conf.noTxAntennas) +
            "Tx antennas. Number of antennas must be within interval [1,4].");

    if (conf.noRxAntennas > 4 || conf.noRxAntennas < 1)
        throw UsrpException(
            "You provided " + std::to_string(conf.noRxAntennas) +
            "Rx antennas. Number of antennas must be in interval [1,4].");
}

std::ostream& operator<<(std::ostream& os, const RfConfig& conf) {
    os << "TxGain: " << conf.txGain << std::endl;
    os << "RxGain: " << conf.rxGain << std::endl;

    os << "TxCarrierFrequency: " << conf.txCarrierFrequency << std::endl;
    os << "RxCarrierFrequency: " << conf.rxCarrierFrequency << std::endl;

    os << "TxAnalogFilterBW: " << conf.txAnalogFilterBw << std::endl;
    os << "RxAnalogFilterBW: " << conf.rxAnalogFilterBw << std::endl;

    os << "TX Sampling Rate: " << conf.txSamplingRate << std::endl;
    os << "RX Sampling Rate: " << conf.rxSamplingRate << std::endl;

    os << "Number of Tx antennas: " << conf.noTxAntennas << std::endl;
    os << "Number of rx antenans: " << conf.noRxAntennas << std::endl;
    return os;
}

void _resizeSignal(MimoSignal& samples, size_t length) {
    for (auto& s : samples) {
        s.resize(length);
    }
}

void extendToWordSize(MimoSignal& samples) {
    _resizeSignal(samples, nextMultipleOfWordSize(samples[0].size()));
}

void shortenSignal(MimoSignal& samples, size_t length) {
    if (samples[0].size() < length)
        throw UsrpException("Signal is too short and cannot be shortened further");
    _resizeSignal(samples, length);
}

void TxStreamingConfig::alignToWordSize() {
    extendToWordSize(samples);
}

size_t RxStreamingConfig::wordAlignedNoSamples() const {
    return nextMultipleOfWordSize(noSamples);
}

}  // namespace bi
