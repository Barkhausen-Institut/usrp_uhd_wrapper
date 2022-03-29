#include "usrp.hpp"

namespace bi {
void Usrp::setRfConfig(const RfConfig& conf) {
    // configure transmitter
    usrpDevice_->set_tx_rate(conf.txSamplingRate);
    usrpDevice_->set_tx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
    uhd::tune_request_t txTuneRequest(conf.txCarrierFrequency);
    usrpDevice_->set_tx_freq(txTuneRequest, 0);
    usrpDevice_->set_tx_gain(conf.txGain, 0);
    usrpDevice_->set_tx_bandwidth(conf.txAnalogFilterBw, 0);

    // configure receiver
    usrpDevice_->set_rx_rate(conf.rxSamplingRate);
    usrpDevice_->set_rx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
    uhd::tune_request_t rxTuneRequest(conf.rxCarrierFrequency);
    usrpDevice_->set_rx_freq(rxTuneRequest, 0);
    usrpDevice_->set_rx_gain(conf.rxGain, 0);
    usrpDevice_->set_rx_bandwidth(conf.rxAnalogFilterBw, 0);

    uhd::stream_args_t txStreamArgs("fc32", "sc16");
    txStreamArgs.channels = std::vector<size_t>({0});
    txStreamer_ = usrpDevice_->get_tx_stream(txStreamArgs);
}

void Usrp::setTxConfig(const TxStreamingConfig& conf) {
    txStreamingConfigs_.push_back(conf);
}

void Usrp::setRxConfig(const RxStreamingConfig& conf) {
    rxStreamingConfigs_.push_back(conf);
}

void Usrp::setTimeToZeroNextPps() {
    usrpDevice_->set_time_next_pps(uhd::time_spec_t(0.f));
    // wait for next pps
    const uhd::time_spec_t lastPpsTime = usrpDevice_->get_time_last_pps();
    while (lastPpsTime == usrpDevice_->get_time_last_pps()) {
    }
}

uint64_t Usrp::getCurrentTime() {
    using namespace std::chrono;
    uint64_t msSinceEpoch =
        duration_cast<milliseconds>(system_clock::now().time_since_epoch())
            .count();
    return msSinceEpoch;
}
std::shared_ptr<UsrpInterface> createUsrp(std::string ip) {
    return std::make_shared<Usrp>(ip);
}
}  // namespace bi
