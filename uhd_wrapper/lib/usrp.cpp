#include <cmath>
#include <numeric>
#include <uhd/types/ref_vector.hpp>

#include "usrp.hpp"

namespace bi {

RfConfig Usrp::getRfConfig() const {
    RfConfig conf;
    std::scoped_lock lock(fpgaAccessMutex_);
    conf.txCarrierFrequency = usrpDevice_->get_tx_freq(0);
    conf.txGain = usrpDevice_->get_tx_gain(0);
    conf.txAnalogFilterBw = usrpDevice_->get_tx_bandwidth(0);
    conf.txSamplingRate = usrpDevice_->get_tx_rate(0);

    conf.rxCarrierFrequency = usrpDevice_->get_rx_freq(0);
    conf.rxGain = usrpDevice_->get_rx_gain(0);
    conf.rxAnalogFilterBw = usrpDevice_->get_rx_bandwidth(0);
    conf.rxSamplingRate = usrpDevice_->get_rx_rate(0);
    conf.noRxAntennas = usrpDevice_->get_rx_subdev_spec().size();
    conf.noTxAntennas = usrpDevice_->get_tx_subdev_spec().size();
    return conf;
}

void Usrp::receive(const double baseTime, std::vector<MimoSignal> &buffers,
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
    buffer = MimoSignal((size_t)rfConfig_.noRxAntennas,
                        samples_vec((size_t)config.noSamples, sample(0, 0)));

    // size_t noPackages = calcNoPackages(config.noSamples, SAMPLES_PER_BUFFER);
    // size_t noSamplesLastBuffer =
    //   calcNoSamplesLastBuffer(config.noSamples, SAMPLES_PER_BUFFER);
    uhd::stream_cmd_t streamCmd =
        uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE;
    streamCmd.num_samps = config.noSamples;
    streamCmd.stream_now = false;
    streamCmd.time_spec = uhd::time_spec_t(baseTime + config.receiveTimeOffset);
    rxStreamer_->issue_stream_cmd(streamCmd);

    uhd::rx_metadata_t mdRx;
    double timeout =
        (baseTime + config.receiveTimeOffset) - getCurrentFpgaTime() + 0.2;
    size_t totalSamplesRecvd = 0;
    size_t remainingNoSamples = config.noSamples;
    size_t noMaxNumSamples = rxStreamer_->get_max_num_samps();
    while (totalSamplesRecvd < config.noSamples) {
        std::vector<sample *> buffers;
        for (int rxAntennaIdx = 0; rxAntennaIdx < rfConfig_.noRxAntennas;
             rxAntennaIdx++) {
            buffers.push_back(buffer[rxAntennaIdx].data() + totalSamplesRecvd);
        }
        remainingNoSamples = config.noSamples - totalSamplesRecvd;
        size_t noSamplesNextPkg = remainingNoSamples < noMaxNumSamples
                                      ? remainingNoSamples
                                      : noMaxNumSamples;
        size_t noSamplesRcvd =
            rxStreamer_->recv(buffers, noSamplesNextPkg, mdRx, timeout, true);

        totalSamplesRecvd += noSamplesRcvd;

        timeout = 0.1f;
        if (mdRx.error_code !=
            uhd::rx_metadata_t::error_code_t::ERROR_CODE_NONE)
            throw UsrpException("error occurred on the receiver: " +
                                mdRx.strerror());
    }
    if (!mdRx.end_of_burst)
        throw UsrpException("I did not receive an end_of_burst.");
}

void Usrp::transmit(const double baseTime, std::exception_ptr &exceptionPtr) {
    try {
        // copy tx streaming configs for exception safety
        std::vector<TxStreamingConfig> txStreamingConfigs =
            std::move(txStreamingConfigs_);
        txStreamingConfigs_ = {};
        for (auto &txStreamingConfig : txStreamingConfigs) {
            processTxStreamingConfig(txStreamingConfig, baseTime);
        }
    } catch (const std::exception &ex) {
        exceptionPtr = std::current_exception();
    }
}

void Usrp::processTxStreamingConfig(const TxStreamingConfig &conf,
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
    double timeout =
        baseTime + conf.sendTimeOffset - getCurrentFpgaTime() + 0.1;

    for (size_t packageIdx = 0; packageIdx < noPackages; packageIdx++) {
        txStreamer_->send(
            {conf.samples[0].data() + packageIdx * SAMPLES_PER_BUFFER},
            packageIdx == (noPackages - 1) ? noSamplesLastBuffer
                                           : SAMPLES_PER_BUFFER,
            mdTx, timeout);
        // mdTx.start_of_burst = false;
        mdTx.has_time_spec = false;
    }
    mdTx.end_of_burst = true;
    txStreamer_->send("", 0, mdTx);
    uhd::async_metadata_t asyncMd;
    // loop through all messages for the ACK packet (may have underflow messages
    // in queue)
    uhd::async_metadata_t::event_code_t lastEventCode =
        uhd::async_metadata_t::EVENT_CODE_BURST_ACK;
    while (txStreamer_->recv_async_msg(asyncMd, timeout)) {
        if (asyncMd.event_code != uhd::async_metadata_t::EVENT_CODE_BURST_ACK)
            lastEventCode = asyncMd.event_code;
        timeout = 0.1f;
    }

    if (lastEventCode != uhd::async_metadata_t::EVENT_CODE_BURST_ACK) {
        throw UsrpException("Error occoured at Tx Streamer with event code: " +
                            std::to_string(lastEventCode));
    }
}
void Usrp::setRfConfig(const RfConfig &conf) {
    std::scoped_lock lock(fpgaAccessMutex_);
    // configure transmitter
    setTxSamplingRate(conf.txSamplingRate);
    uhd::tune_request_t txTuneRequest(conf.txCarrierFrequency);
    usrpDevice_->set_tx_freq(txTuneRequest, 0);
    usrpDevice_->set_tx_gain(conf.txGain, 0);
    usrpDevice_->set_tx_bandwidth(conf.txAnalogFilterBw, 0);

    // configure receiver
    for (int idxRxAntenna = 0; idxRxAntenna < conf.noRxAntennas;
         idxRxAntenna++) {
        setRfConfigForRxAntenna(conf, idxRxAntenna);
    }
    usrpDevice_->set_time_now(uhd::time_spec_t(0.0));
    if (!subdevSpecSet_) {
        usrpDevice_->set_rx_subdev_spec(
            uhd::usrp::subdev_spec_t(SUBDEV_SPECS[conf.noRxAntennas - 1]), 0);
        usrpDevice_->set_tx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
        subdevSpecSet_ = true;
    }

    if (!txStreamer_) {
        uhd::stream_args_t txStreamArgs("fc32", "");
        txStreamArgs.channels = std::vector<size_t>({0});
        txStreamer_ = usrpDevice_->get_tx_stream(txStreamArgs);
    }
    if (rxStreamer_) rxStreamer_.reset();
    uhd::stream_args_t rxStreamArgs("fc32", "");
    rxStreamArgs.channels = std::vector<size_t>(conf.noRxAntennas, 0);
    std::iota(rxStreamArgs.channels.begin(), rxStreamArgs.channels.end(), 0);
    rxStreamer_ = usrpDevice_->get_rx_stream(rxStreamArgs);

    rfConfig_ = getRfConfig();
}

void Usrp::setRfConfigForRxAntenna(const RfConfig &conf, size_t rxAntennaIdx) {
    setRxSamplingRate(conf.rxSamplingRate, rxAntennaIdx);
    uhd::tune_request_t rxTuneRequest(conf.rxCarrierFrequency);
    usrpDevice_->set_rx_freq(rxTuneRequest, rxAntennaIdx);
    usrpDevice_->set_rx_gain(conf.rxGain, rxAntennaIdx);
    usrpDevice_->set_rx_bandwidth(conf.rxAnalogFilterBw, rxAntennaIdx);
}

void Usrp::setTxConfig(const TxStreamingConfig &conf) {
    assertValidTxSignal(conf.samples, MAX_SAMPLES_TX_SIGNAL);
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
    return;
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

void Usrp::execute(const double baseTime) {
    receivedSamples_ = {{{}}};
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

void Usrp::resetSyncSources() {
    usrpDevice_->set_sync_source("internal", "internal");
}
void Usrp::resetStreamingConfigs() {
    txStreamingConfigs_ = {};
    rxStreamingConfigs_ = {};
}
void Usrp::setTxSamplingRate(const double samplingRate) {
    usrpDevice_->set_tx_rate(samplingRate);
    double actualSamplingRate = usrpDevice_->get_tx_rate();
    assertSamplingRate(actualSamplingRate, masterClockRate_);
}
void Usrp::setRxSamplingRate(const double samplingRate, size_t idxRxAntenna) {
    usrpDevice_->set_rx_rate(samplingRate, idxRxAntenna);
    double actualSamplingRate = usrpDevice_->get_rx_rate(idxRxAntenna);
    assertSamplingRate(actualSamplingRate, masterClockRate_);
}

}  // namespace bi
