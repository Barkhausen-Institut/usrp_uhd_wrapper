#include <cmath>

#include "usrp.hpp"

namespace bi {

RfConfig Usrp::getRfConfig() const {
    RfConfig conf;
    std::scoped_lock lock(fpgaAccessMutex_);
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

void Usrp::receive(const float baseTime, std::vector<MimoSignal> &buffers,
                   std::exception_ptr &exceptionPtr) {
    try {
        std::vector<RxStreamingConfig> rxStreamingConfigs =
            std::move(rxStreamingConfigs_);
        rxStreamingConfigs_ = {};
        for (size_t configIdx = 0; configIdx < rxStreamingConfigs.size();
             configIdx++) {
            processRxStreamingConfig(rxStreamingConfigs[configIdx],
                                     buffers[configIdx], baseTime);
        }
    } catch (const std::exception &ex) {
        exceptionPtr = std::current_exception();
    }
}

void Usrp::processRxStreamingConfig(const RxStreamingConfig &config,
                                    MimoSignal &buffer, const double baseTime) {
    buffer[0].resize(config.noSamples);

    size_t noPackages = calcNoPackages(config.noSamples, SAMPLES_PER_BUFFER);
    size_t noSamplesLastBuffer =
        calcNoSamplesLastBuffer(config.noSamples, SAMPLES_PER_BUFFER);

    uhd::stream_cmd_t streamCmd =
        uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE;
    streamCmd.time_spec = uhd::time_spec_t(baseTime + config.receiveTimeOffset);
    streamCmd.num_samps = config.noSamples;
    streamCmd.stream_now = false;
    rxStreamer_->issue_stream_cmd(streamCmd);

    uhd::rx_metadata_t mdRx;
    double timeout =
        (baseTime + config.receiveTimeOffset) - getCurrentFpgaTime() + 0.2;
    for (size_t packageIdx = 0; packageIdx < noPackages; packageIdx++) {
        rxStreamer_->recv({buffer[0].data() + packageIdx * SAMPLES_PER_BUFFER},
                          packageIdx == (noPackages - 1) ? noSamplesLastBuffer
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
}

void Usrp::transmit(const float baseTime, std::exception_ptr &exceptionPtr) {
    try {
        // copy tx streaming configs for exception safety
        std::vector<TxStreamingConfig> txStreamingConfigs =
            std::move(txStreamingConfigs_);
        txStreamingConfigs_ = {};
        for (auto &txStreamingConfig : txStreamingConfigs) {
            assertValidTxSignal(txStreamingConfig.samples,
                                MAX_SAMPLES_TX_SIGNAL);
            processTxStremaingConfig(txStreamingConfig, baseTime);
        }
    } catch (const std::exception &ex) {
        exceptionPtr = std::current_exception();
    }
}

void Usrp::processTxStremaingConfig(const TxStreamingConfig &conf,
                                    const double baseTime) {
    size_t noPackages =
        calcNoPackages(conf.samples[0].size(), SAMPLES_PER_BUFFER);
    size_t noSamplesLastBuffer =
        calcNoSamplesLastBuffer(conf.samples[0].size(), SAMPLES_PER_BUFFER);

    // specifiy on specifications of how to stream the command
    uhd::tx_metadata_t mdTx;
    mdTx.start_of_burst = false;
    mdTx.end_of_burst = false;
    mdTx.has_time_spec = true;

    mdTx.time_spec = uhd::time_spec_t(baseTime + conf.sendTimeOffset);

    for (size_t packageIdx = 0; packageIdx < noPackages; packageIdx++) {
        txStreamer_->send(
            {conf.samples[0].data() + packageIdx * SAMPLES_PER_BUFFER},
            packageIdx == (noPackages - 1) ? noSamplesLastBuffer
                                           : SAMPLES_PER_BUFFER,
            mdTx, 0.1f);
        // mdTx.start_of_burst = false;
        mdTx.has_time_spec = false;
    }
    mdTx.end_of_burst = true;
    txStreamer_->send("", 0, mdTx);
}
void Usrp::setRfConfig(const RfConfig &conf) {
    std::scoped_lock lock(fpgaAccessMutex_);
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

    rfConfig_ = getRfConfig();
}

void Usrp::setTxConfig(const TxStreamingConfig &conf) {
    if (txStreamingConfigs_.size() > 0)
        assertValidTxStreamingConfig(txStreamingConfigs_.back(), conf,
                                     GUARD_OFFSET_S_, rfConfig_.txSamplingRate);
    txStreamingConfigs_.push_back(conf);
}

void Usrp::setRxConfig(const RxStreamingConfig &conf) {
    if (rxStreamingConfigs_.size() > 0)
        assertValidRxStreamingConfig(rxStreamingConfigs_.back(), conf,
                                     GUARD_OFFSET_S_, rfConfig_.rxSamplingRate);
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
    std::scoped_lock lock(fpgaAccessMutex_);
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
    std::scoped_lock lock(fpgaAccessMutex_);
    if (!ppsSetToZero_) {
        setTimeToZeroNextPpsThread_.join();
    }
    return usrpDevice_->get_time_now().get_real_secs();
}

void Usrp::execute(const float baseTime) {
    // const double fpgaTimeThreadStart = getCurrentFpgaTime();
    if (!ppsSetToZero_) {
        throw UsrpException("Synchronization must happen before execution.");
    } else {
        transmitThread_ = std::thread(&Usrp::transmit, this, baseTime,
                                      std::ref(transmitThreadException_));
        receiveThread_ = std::thread(&Usrp::receive, this, baseTime,
                                     std::ref(receivedSamples_),
                                     std::ref(receiveThreadException_));
    }
}

std::vector<MimoSignal> Usrp::collect() {
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
