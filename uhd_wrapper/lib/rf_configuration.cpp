#include "rf_configuration.hpp"
#include "usrp_exception.hpp"

namespace bi {


RFConfiguration::RFConfiguration(const RfNocBlockConfig& blockNames,
                                 uhd::rfnoc::rfnoc_graph::sptr graph)
    : RfNocBlocks(blockNames, graph) {
    masterClockRate_ = 245.76e6; // TODO!
    //masterClockRate_ = usrpDevice_->get_master_clock_rate();
}

void RFConfiguration::setRfConfig(const RfConfig &conf) {
    assertValidRfConfig(conf);

    for (int idxRxAntenna = 0; idxRxAntenna < conf.noRxAntennas; idxRxAntenna++)
        setRfConfigForRxAntenna(conf, idxRxAntenna);

    for (int idxTxAntenna = 0; idxTxAntenna < conf.noTxAntennas; idxTxAntenna++)
        setRfConfigForTxAntenna(conf, idxTxAntenna);

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

    assertSamplingRate(conf.rxSamplingRate, masterClockRate_);
    auto [ddc, ddcchannel] = getDDCChannelPair(rxAntennaIdx);
    ddc->set_output_rate(conf.rxSamplingRate, ddcchannel);
}

void RFConfiguration::setRxSampleRate(double rate) {
    if (rfConfig_.noRxAntennas == 0)
        throw UsrpException("Cannot set sample rate without knowning number of antennas");
    assertSamplingRate(rate, masterClockRate_);

    for(int ant = 0; ant < rfConfig_.noRxAntennas; ant++) {
      auto [ddc, channel] = getDDCChannelPair(ant);
      ddc->set_output_rate(rate, channel);
    }
}


void RFConfiguration::setRfConfigForTxAntenna(const RfConfig &conf,
                                              const size_t txAntennaIdx) {
    auto [radio, channel] = getRadioChannelPair(txAntennaIdx);
    radio->set_tx_frequency(conf.txCarrierFrequency, channel);
    radio->set_tx_gain(conf.txGain, channel);
    radio->set_tx_bandwidth(conf.txAnalogFilterBw, channel);

    assertSamplingRate(conf.txSamplingRate, masterClockRate_);
    auto [duc, ducchannel] = getDUCChannelPair(txAntennaIdx);
    duc->set_input_rate(conf.txSamplingRate, ducchannel);
}

void RFConfiguration::setTxSampleRate(double rate) {
    if (rfConfig_.noTxAntennas == 0)
        throw UsrpException("Cannot set sample rate without knowning number of antennas");
    assertSamplingRate(rate, masterClockRate_);

    for(int ant = 0; ant < rfConfig_.noTxAntennas; ant++) {
      auto [duc, channel] = getDUCChannelPair(ant);
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

RfConfig RFConfiguration::readFromGraph() {
    RfConfig conf;
    conf.txCarrierFrequency = radioCtrl1_->get_tx_frequency(0);
    conf.txGain = radioCtrl1_->get_tx_gain(0);
    conf.txAnalogFilterBw = radioCtrl1_->get_tx_bandwidth(0);
    conf.txSamplingRate = ducControl1_->get_input_rate(0);

    conf.rxCarrierFrequency = radioCtrl1_->get_rx_frequency(0);
    conf.rxGain = radioCtrl1_->get_rx_gain(0);
    conf.rxAnalogFilterBw = radioCtrl1_->get_rx_bandwidth(0);
    conf.rxSamplingRate = ddcControl1_->get_output_rate(0);

    // TODO!
    conf.noRxAntennas = 1;
    conf.noTxAntennas = 1;
    //conf.noRxAntennas = usrpDevice_->get_rx_subdev_spec().size();
    //conf.noTxAntennas = usrpDevice_->get_tx_subdev_spec().size();
    return conf;
}

RFConfiguration::DDCChannelPair RFConfiguration::getDDCChannelPair(int antenna) {
    if (antenna < 2)
        return {ddcControl1_, antenna};
    else
        return {ddcControl2_, antenna - 2};
}

RFConfiguration::DUCChannelPair RFConfiguration::getDUCChannelPair(int antenna) {
    if (antenna < 2)
        return {ducControl1_, antenna};
    else
        return {ducControl2_, antenna - 2};
}
}
