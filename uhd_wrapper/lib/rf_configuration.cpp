#include "rf_configuration.hpp"
#include "usrp_exception.hpp"

namespace bi {


RFConfiguration::RFConfiguration(const RfNocBlockConfig& blockNames,
                                 uhd::rfnoc::rfnoc_graph::sptr graph,
                                 const StreamMapper& streamMapper)
    : RfNocBlocks(blockNames, graph), streamMapper_(streamMapper) {
    masterClockRate_ = radioCtrl1_->get_tick_rate();
}

void RFConfiguration::setRfConfig(const RfConfig &conf) {
    assertValidRfConfig(conf);

    numTxAntennas_ = conf.noTxAntennas;
    numRxAntennas_ = conf.noRxAntennas;

    for (int idxRxAntenna = 0; idxRxAntenna < numRxAntennas_; idxRxAntenna++)
        setRfConfigForRxAntenna(conf,
                                streamMapper_.mapRxStreamToAntenna(idxRxAntenna));
    setRxSampleRate(conf.rxSamplingRate);

    for (int idxTxAntenna = 0; idxTxAntenna < numTxAntennas_; idxTxAntenna++)
        setRfConfigForTxAntenna(conf,
                                streamMapper_.mapTxStreamToAntenna(idxTxAntenna));
    setTxSampleRate(conf.txSamplingRate);

    rfConfig_ = readFromGraph();
    if (rfConfig_ != conf) {
        std::ostringstream confStream;
        confStream << "Actual Rf Config:" << std::endl
                   << rfConfig_ << std::endl
                   << std::endl
                   << "Requested Rf Config: " << conf << std::endl;
        throw UsrpException("Request and actual Rf Config mismatch:\n " +
                            confStream.str());
    }
}

void RFConfiguration::setRfConfigForRxAntenna(const RfConfig &conf,
                                              const size_t rxAntennaIdx) {
    auto [radio, channel] = getRadioChannelPair(rxAntennaIdx);
    radio->set_rx_frequency(conf.rxCarrierFrequency, channel);
    radio->set_rx_gain(conf.rxGain, channel);
    radio->set_rx_bandwidth(conf.rxAnalogFilterBw, channel);
}

void RFConfiguration::setRxSampleRate(double rate) {
    if (numRxAntennas_ == 0)
        throw UsrpException("Cannot set sample rate without knowning number of antennas");
    assertSamplingRate(rate, masterClockRate_, supportsDecimation());

    if (!supportsDecimation())
        return;

    for(int ant = 0; ant < numRxAntennas_; ant++) {
      auto [ddc, channel] = getDDCChannelPair(streamMapper_.mapRxStreamToAntenna(ant));
      ddc->set_output_rate(rate, channel);
    }
}


void RFConfiguration::setRfConfigForTxAntenna(const RfConfig &conf,
                                              const size_t txAntennaIdx) {
    auto [radio, channel] = getRadioChannelPair(txAntennaIdx);
    radio->set_tx_frequency(conf.txCarrierFrequency, channel);
    radio->set_tx_gain(conf.txGain, channel);
    radio->set_tx_bandwidth(conf.txAnalogFilterBw, channel);
}

void RFConfiguration::setTxSampleRate(double rate) {
    if (numTxAntennas_ == 0)
        throw UsrpException("Cannot set sample rate without knowning number of antennas");
    assertSamplingRate(rate, masterClockRate_, supportsDecimation());

    if (!supportsDecimation())
        return;

    for(int ant = 0; ant < numTxAntennas_; ant++) {
      auto [duc, channel] = getDUCChannelPair(streamMapper_.mapTxStreamToAntenna(ant));
      duc->set_input_rate(rate, channel);
    }
}

void RFConfiguration::renewSampleRateSettings() {
    setRxSampleRate(rfConfig_.rxSamplingRate);
    setTxSampleRate(rfConfig_.txSamplingRate);
}

int RFConfiguration::getNumTxAntennas() const {
    return rfConfig_.noTxAntennas;
}

int RFConfiguration::getNumRxAntennas() const {
    return rfConfig_.noRxAntennas;
}

double RFConfiguration::getTxSamplingRate() const {
    return rfConfig_.txSamplingRate;
}

double RFConfiguration::getRxSamplingRate() const {
    return rfConfig_.rxSamplingRate;
}

int RFConfiguration::getRxDecimationRatio() const {
    if (supportsDecimation())
        return ddcControl1_->get_property<int>("decim", 0);
    else
        return 1;
}

double RFConfiguration::getMasterClockRate() const {
    return masterClockRate_;
}

std::vector<double> RFConfiguration::getSupportedSampleRates() const {
    double master = getMasterClockRate();
    std::vector<double> result = { master };
    if (supportsDecimation()) {
        for(int i = 2; i < 58; i += 2)
            result.push_back(master / i);
    }
    return result;
}

RfConfig RFConfiguration::readFromGraph() {
    RfConfig conf;
    auto [rxRadio, rxChan] = getRadioChannelPair(streamMapper_.mapRxStreamToAntenna(0));
    auto [txRadio, txChan] = getRadioChannelPair(streamMapper_.mapTxStreamToAntenna(0));

    conf.txCarrierFrequency = txRadio->get_tx_frequency(txChan);
    conf.txGain = txRadio->get_tx_gain(txChan);
    conf.txAnalogFilterBw = txRadio->get_tx_bandwidth(txChan);
    conf.txSamplingRate = readTxSampleRate();

    conf.rxCarrierFrequency = rxRadio->get_rx_frequency(rxChan);
    conf.rxGain = rxRadio->get_rx_gain(rxChan);
    conf.rxAnalogFilterBw = rxRadio->get_rx_bandwidth(rxChan);
    conf.rxSamplingRate = readRxSampleRate();

    // TODO!
    conf.noTxAntennas = numTxAntennas_;
    conf.noRxAntennas = numRxAntennas_;
    //conf.noRxAntennas = usrpDevice_->get_rx_subdev_spec().size();
    //conf.noTxAntennas = usrpDevice_->get_tx_subdev_spec().size();
    return conf;
}

RFConfiguration::DDCChannelPair RFConfiguration::getDDCChannelPair(int antenna) const {
    int numAntennasPerRadio = radioCtrl1_->get_num_input_ports();
    if (antenna < numAntennasPerRadio)
        return {ddcControl1_, antenna};
    else
        return {ddcControl2_, antenna - numAntennasPerRadio};
}

RFConfiguration::DUCChannelPair RFConfiguration::getDUCChannelPair(int antenna) const {
    int numAntennasPerRadio = radioCtrl1_->get_num_input_ports();
    if (antenna < numAntennasPerRadio)
        return {ducControl1_, antenna};
    else
        return {ducControl2_, antenna - numAntennasPerRadio};
}

double RFConfiguration::readRxSampleRate() const {
    if (supportsDecimation()) {
        auto [ddc, chan] = getDDCChannelPair(streamMapper_.mapRxStreamToAntenna(0));
        return ddc->get_output_rate(chan);
    }
    else
        return getMasterClockRate();
}

double RFConfiguration::readTxSampleRate() const {
    if (supportsDecimation()) {
        auto [duc, chan] = getDUCChannelPair(streamMapper_.mapTxStreamToAntenna(0));
        return duc->get_input_rate(chan);
    }
    else
        return getMasterClockRate();
}
}
