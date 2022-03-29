#include "usrp.hpp"

ErrorCode Usrp::setRfConfig(const RfConfig& conf) {
    // init usrp
    ErrorCode retCode = SUCCESS;

    // configure transmitter
    usrp_->set_tx_rate(conf.txSamplingRate);
    usrp_->set_tx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
    uhd::tune_request_t txTuneRequest(conf.txCarrierFrequency);
    usrp_->set_tx_freq(txTuneRequest, 0);
    usrp_->set_tx_gain(conf.txGain, 0);
    usrp_->set_tx_bandwidth(conf.txAnalogFilterBw, 0);

    // configure receiver
    usrp_->set_rx_rate(conf.rxSamplingRate);
    usrp_->set_rx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
    uhd::tune_request_t rxTuneRequest(conf.rxCarrierFrequency);
    usrp_->set_rx_freq(rxTuneRequest, 0);
    usrp_->set_rx_gain(conf.rxGain, 0);
    usrp_->set_rx_bandwidth(conf.rxAnalogFilterBw, 0);
    return retCode;
}

ErrorCode Usrp::setTxConfig(const TxStreamingConfig& conf) {
    txStreamingConfigs_.push_back(conf);
    // validate here?
}

ErrorCode Usrp::setRxConfig(const RxStreamingConfig& conf) {
    rxStreamingConfigs_.push_back(conf);
    // balidate here?
}

ErrorCode Usrp::setTimeToZeroNextPps() {
    usrp_->set_time_next_pps(uhd::time_spec_t(0.f));
    // wait for next pps
    const uhd::time_spec_t last_pps_time = usrp_->get_time_last_pps();
    while (last_pps_time == usrp_->get_time_last_pps()) {
    }
}

std::shared_ptr<UsrpInterface> createUsrp(std::string ip) {
    return std::make_shared<Usrp>(ip);
}