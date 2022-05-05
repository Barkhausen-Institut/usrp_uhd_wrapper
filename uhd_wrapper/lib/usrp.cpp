#include <cmath>

#include "usrp.hpp"

namespace bi {

RfConfig Usrp::getRfConfig() const {
    RfConfig conf;
    conf.txCarrierFrequency.push_back(usrpDevice_->get_tx_freq(0));
    conf.txGain.push_back(usrpDevice_->get_tx_gain(0));
    conf.txAnalogFilterBw = usrpDevice_->get_tx_bandwidth(0);
    conf.txSamplingRate = usrpDevice_->get_tx_rate(0);

    conf.rxCarrierFrequency.push_back(usrpDevice_->get_rx_freq(0));
    conf.rxGain.push_back(usrpDevice_->get_rx_gain(0));
    conf.rxAnalogFilterBw = usrpDevice_->get_rx_bandwidth(0);
    conf.rxSamplingRate = usrpDevice_->get_rx_rate(0);

    return conf;
}

void Usrp::receive(const float baseTime,
                   std::vector<std::vector<samples_vec>> &buffers,
                   std::exception_ptr &exceptionPtr,
                   const double fpgaTimeThreadStart) {
    try {
        size_t configIdx = 0;
        while (rxStreamingConfigs_.size() != 0) {
            RxStreamingConfig rxStreamingConfig = rxStreamingConfigs_[0];
            buffers[configIdx][0].resize(rxStreamingConfig.noSamples);

            size_t noPackages =
                calcNoPackages(rxStreamingConfig.noSamples, SAMPLES_PER_BUFFER);
            size_t noSamplesLastBuffer = calcNoSamplesLastBuffer(
                rxStreamingConfig.noSamples, SAMPLES_PER_BUFFER);

            uhd::stream_cmd_t streamCmd =
                uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE;
            streamCmd.time_spec = uhd::time_spec_t(
                baseTime + rxStreamingConfig.receiveTimeOffset);
            streamCmd.num_samps = rxStreamingConfig.noSamples;
            streamCmd.stream_now = false;
            rxStreamer_->issue_stream_cmd(streamCmd);

            uhd::rx_metadata_t mdRx;
            double timeout = (baseTime + rxStreamingConfig.receiveTimeOffset) -
                             fpgaTimeThreadStart + 0.2;
            for (size_t packageIdx = 0; packageIdx < noPackages; packageIdx++) {
                rxStreamer_->recv({buffers[configIdx][0].data() +
                                   packageIdx * SAMPLES_PER_BUFFER},
                                  packageIdx == (noPackages - 1)
                                      ? noSamplesLastBuffer
                                      : SAMPLES_PER_BUFFER,
                                  mdRx, timeout);

                timeout = 0.1f;
                if (mdRx.error_code !=
                    uhd::rx_metadata_t::error_code_t::ERROR_CODE_NONE)
                    throw UsrpException("error occurred on the receiver: " +
                                        mdRx.strerror());
            }
            if (!mdRx.end_of_burst)
                throw UsrpException("I did not receive an end_of_burst.");
            rxStreamingConfigs_.erase(rxStreamingConfigs_.begin());
        }
    } catch (const std::exception &ex) {
        exceptionPtr = std::current_exception();
    }
}

void Usrp::transmit(const float baseTime, std::exception_ptr &exceptionPtr,
                    const double fpgaTimeThreadStart) {
    // assume one txStreamConfig for the moment....
    try {
        while (txStreamingConfigs_.size() != 0) {
            // add helpers
            TxStreamingConfig txStreamingConfig = txStreamingConfigs_[0];
            size_t noPackages = calcNoPackages(
                txStreamingConfig.samples[0].size(), SAMPLES_PER_BUFFER);
            size_t noSamplesLastBuffer = calcNoSamplesLastBuffer(
                txStreamingConfig.samples[0].size(), SAMPLES_PER_BUFFER);

            // specifiy on specifications of how to stream the command
            uhd::tx_metadata_t mdTx;
            mdTx.start_of_burst = false;
            mdTx.end_of_burst = false;
            mdTx.has_time_spec = true;

            mdTx.time_spec =
                uhd::time_spec_t(baseTime + txStreamingConfig.sendTimeOffset);

            for (size_t packageIdx = 0; packageIdx < noPackages; packageIdx++) {
                txStreamer_->send({txStreamingConfig.samples[0].data() +
                                   packageIdx * SAMPLES_PER_BUFFER},
                                  packageIdx == (noPackages - 1)
                                      ? noSamplesLastBuffer
                                      : SAMPLES_PER_BUFFER,
                                  mdTx, 0.1f);
                // mdTx.start_of_burst = false;
                mdTx.has_time_spec = false;
            }
            mdTx.end_of_burst = true;
            txStreamer_->send("", 0, mdTx);
            txStreamingConfigs_.erase(txStreamingConfigs_.begin());
        }
    } catch (const std::exception &ex) {
        exceptionPtr = std::current_exception();
    }
}
void Usrp::setRfConfig(const RfConfig &conf) {
    // configure transmitter
    setTxSamplingRate(conf.txSamplingRate);
    uhd::tune_request_t txTuneRequest(conf.txCarrierFrequency[0]);
    usrpDevice_->set_tx_freq(txTuneRequest, 0);
    usrpDevice_->set_tx_gain(conf.txGain[0], 0);
    usrpDevice_->set_tx_bandwidth(conf.txAnalogFilterBw, 0);

    // configure receiver
    setRxSamplingRate(conf.rxSamplingRate);
    uhd::tune_request_t rxTuneRequest(conf.rxCarrierFrequency[0]);
    usrpDevice_->set_rx_freq(rxTuneRequest, 0);
    usrpDevice_->set_rx_gain(conf.rxGain[0], 0);
    usrpDevice_->set_rx_bandwidth(conf.rxAnalogFilterBw, 0);

    if (!subdevSpecSet_) {
        usrpDevice_->set_rx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
        usrpDevice_->set_tx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
        subdevSpecSet_ = true;
    }

    if (!txStreamer_) {
        uhd::stream_args_t txStreamArgs("fc32", "sc16");
        txStreamArgs.channels = std::vector<size_t>({0});
        txStreamer_ = usrpDevice_->get_tx_stream(txStreamArgs);
    }
    if (!rxStreamer_) {
        uhd::stream_args_t rxStreamArgs("fc32", "sc16");
        rxStreamArgs.channels = std::vector<size_t>({0});
        rxStreamer_ = usrpDevice_->get_rx_stream(rxStreamArgs);
    }
}

void Usrp::setTxConfig(const TxStreamingConfig &conf) {
    txStreamingConfigs_.push_back(conf);
}

void Usrp::setRxConfig(const RxStreamingConfig &conf) {
    rxStreamingConfigs_.push_back(conf);
}

void Usrp::setTimeToZeroNextPps() {
    // join previous thread to make sure it has properly ended. This is also
    // necessary to use op= below (it'll std::terminate() if not joined
    // before)
    if (setTimeToZeroNextPpsThread_.joinable())
        setTimeToZeroNextPpsThread_.join();

    setTimeToZeroNextPpsThread_ =
        std::thread(&Usrp::setTimeToZeroNextPpsThreadFunction, this);
}

void Usrp::setTimeToZeroNextPpsThreadFunction() {
    ppsSetToZero_ = false;
    usrpDevice_->set_time_next_pps(uhd::time_spec_t(0.f));
    // wait for next pps
    const uhd::time_spec_t lastPpsTime = usrpDevice_->get_time_last_pps();
    while (lastPpsTime == usrpDevice_->get_time_last_pps()) {
    }
    ppsSetToZero_ = true;
}

uint64_t Usrp::getCurrentSystemTime() {
    using namespace std::chrono;
    uint64_t msSinceEpoch =
        duration_cast<milliseconds>(system_clock::now().time_since_epoch())
            .count();
    return msSinceEpoch;
}

double Usrp::getCurrentFpgaTime() {
    if (!ppsSetToZero_) {
        setTimeToZeroNextPpsThread_.join();
    }
    return usrpDevice_->get_time_now().get_real_secs();
}

void Usrp::execute(const float baseTime) {
    const double fpgaTimeThreadStart = getCurrentFpgaTime();
    if (!ppsSetToZero_) {
        throw UsrpException("Synchronization must happen before execution.");
    } else {
        transmitThread_ = std::thread(&Usrp::transmit, this, baseTime,
                                      std::ref(transmitThreadException_),
                                      fpgaTimeThreadStart);
        receiveThread_ = std::thread(
            &Usrp::receive, this, baseTime, std::ref(receivedSamples_),
            std::ref(receiveThreadException_), fpgaTimeThreadStart);
    }
}

std::vector<std::vector<samples_vec>> Usrp::collect() {
    transmitThread_.join();
    receiveThread_.join();
    if (transmitThreadException_)
        std::rethrow_exception(transmitThreadException_);
    if (receiveThreadException_)
        std::rethrow_exception(receiveThreadException_);
    return receivedSamples_;
}
std::unique_ptr<UsrpInterface> createUsrp(const std::string &ip) {
    return std::make_unique<Usrp>(ip);
}

void Usrp::reset() { usrpDevice_->set_sync_source("internal", "internal"); }
void Usrp::setTxSamplingRate(const double samplingRate) {
    usrpDevice_->set_tx_rate(samplingRate);
    double actualSamplingRate = usrpDevice_->get_tx_rate();
    assertSamplingRate(actualSamplingRate, masterClockRate_);
}
void Usrp::setRxSamplingRate(const double samplingRate) {
    usrpDevice_->set_rx_rate(samplingRate);
    double actualSamplingRate = usrpDevice_->get_rx_rate();
    assertSamplingRate(actualSamplingRate, masterClockRate_);
}

}  // namespace bi
