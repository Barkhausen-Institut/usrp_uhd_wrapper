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
    conf.txCarrierFrequency = radioCtrl1_->get_tx_frequency(0);
    conf.txGain = radioCtrl1_->get_tx_gain(0);
    conf.txAnalogFilterBw = radioCtrl1_->get_tx_bandwidth(0);
    conf.txSamplingRate = readTxSampleRate();

    conf.rxCarrierFrequency = radioCtrl1_->get_rx_frequency(0);
    conf.rxGain = radioCtrl1_->get_rx_gain(0);
    conf.rxAnalogFilterBw = radioCtrl1_->get_rx_bandwidth(0);
    conf.rxSamplingRate = readRxSampleRate();

    // TODO!
    conf.noTxAntennas = numTxAntennas_;
    conf.noRxAntennas = numRxAntennas_;
    //conf.noRxAntennas = usrpDevice_->get_rx_subdev_spec().size();
    //conf.noTxAntennas = usrpDevice_->get_tx_subdev_spec().size();
    return conf;
}

RFConfiguration::DDCChannelPair RFConfiguration::getDDCChannelPair(int antenna) {
    int numAntennasPerRadio = radioCtrl1_->get_num_input_ports();
    if (antenna < numAntennasPerRadio)
        return {ddcControl1_, antenna};
    else
        return {ddcControl2_, antenna - numAntennasPerRadio};
}

RFConfiguration::DUCChannelPair RFConfiguration::getDUCChannelPair(int antenna) {
    int numAntennasPerRadio = radioCtrl1_->get_num_input_ports();
    if (antenna < numAntennasPerRadio)
        return {ducControl1_, antenna};
    else
        return {ducControl2_, antenna - numAntennasPerRadio};
}

double RFConfiguration::readRxSampleRate() const {
    if (supportsDecimation())
        return ddcControl1_->get_output_rate(0);
    else
        return getMasterClockRate();
}

double RFConfiguration::readTxSampleRate() const {
    if (supportsDecimation())
        return ducControl1_->get_input_rate(0);
    else
        return getMasterClockRate();
}
}
