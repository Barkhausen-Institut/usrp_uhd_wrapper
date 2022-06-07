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
        buffers.resize(rxStreamingConfigs.size());
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
    size_t maxPacketSize = rxStreamer_->get_max_num_samps();

    while (totalSamplesRecvd < config.noSamples) {
        std::vector<sample *> buffers;
        for (int rxAntennaIdx = 0; rxAntennaIdx < rfConfig_.noRxAntennas;
             rxAntennaIdx++) {
            buffers.push_back(buffer[rxAntennaIdx].data() + totalSamplesRecvd);
        }
        size_t remainingNoSamples = config.noSamples - totalSamplesRecvd;
        size_t noSamplesNextPkg = std::min(remainingNoSamples, maxPacketSize);
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
    // specifiy on specifications of how to stream the command
    uhd::tx_metadata_t mdTx;
    mdTx.start_of_burst = false;
    mdTx.end_of_burst = false;
    mdTx.has_time_spec = true;

    mdTx.time_spec = uhd::time_spec_t(baseTime + conf.sendTimeOffset);
    double timeout =
        baseTime + conf.sendTimeOffset - getCurrentFpgaTime() + 0.1;

    size_t totalSamplesSent = 0;
    size_t noSampsTxSignal = conf.samples[0].size();
    size_t maxPacketSize = txStreamer_->get_max_num_samps();

    while (totalSamplesSent < noSampsTxSignal) {
        std::vector<const sample *> buffers;
        for (int txAntennaIdx = 0; txAntennaIdx < rfConfig_.noTxAntennas;
             txAntennaIdx++)
            buffers.push_back(conf.samples[txAntennaIdx].data() +
                              totalSamplesSent);
        size_t sampsToSend =
            std::min(noSampsTxSignal - totalSamplesSent, maxPacketSize);
        size_t samplesSent =
            txStreamer_->send(buffers, sampsToSend, mdTx, timeout);
        mdTx.has_time_spec = false;

        totalSamplesSent += samplesSent;
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
    assertValidRfConfig(conf);
    std::scoped_lock lock(fpgaAccessMutex_);

    for (int idxRxAntenna = 0; idxRxAntenna < conf.noRxAntennas; idxRxAntenna++)
        setRfConfigForRxAntenna(conf, idxRxAntenna);

    for (int idxTxAntenna = 0; idxTxAntenna < conf.noTxAntennas; idxTxAntenna++)
        setRfConfigForTxAntenna(conf, idxTxAntenna);

    if (!subdevSpecSet_) {
        usrpDevice_->set_rx_subdev_spec(
            uhd::usrp::subdev_spec_t(SUBDEV_SPECS[conf.noRxAntennas - 1]), 0);
        usrpDevice_->set_tx_subdev_spec(
            uhd::usrp::subdev_spec_t(SUBDEV_SPECS[conf.noTxAntennas - 1]), 0);
        subdevSpecSet_ = true;
    }
    configureTxStreamer(conf);

    rfConfig_ = getRfConfig();
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

void Usrp::configureRxStreamer(const RfConfig &conf) {
    if (rxStreamer_) rxStreamer_.reset();
    uhd::stream_args_t rxStreamArgs("fc32", "sc16");
    rxStreamArgs.channels = std::vector<size_t>({});
    for (int rxAntennaIdx = 0; rxAntennaIdx < conf.noRxAntennas; rxAntennaIdx++)
        rxStreamArgs.channels.push_back(rxAntennaIdx);
    rxStreamer_ = usrpDevice_->get_rx_stream(rxStreamArgs);
}

void Usrp::configureTxStreamer(const RfConfig &conf) {
    if (!txStreamer_) {
        uhd::stream_args_t txStreamArgs("fc32", "sc16");
        txStreamArgs.channels = std::vector<size_t>({});

        for (int txAntennaIdx = 0; txAntennaIdx < conf.noTxAntennas;
             txAntennaIdx++)
            txStreamArgs.channels.push_back(txAntennaIdx);
        txStreamer_ = usrpDevice_->get_tx_stream(txStreamArgs);
    }
}
void Usrp::setRfConfigForRxAntenna(const RfConfig &conf,
                                   const size_t rxAntennaIdx) {
    setRxSamplingRate(conf.rxSamplingRate, rxAntennaIdx);
    uhd::tune_request_t rxTuneRequest(conf.rxCarrierFrequency);
    usrpDevice_->set_rx_freq(rxTuneRequest, rxAntennaIdx);
    usrpDevice_->set_rx_gain(conf.rxGain, rxAntennaIdx);
    usrpDevice_->set_rx_bandwidth(conf.rxAnalogFilterBw, rxAntennaIdx);
}

void Usrp::setRfConfigForTxAntenna(const RfConfig &conf,
                                   const size_t txAntennaIdx) {
    setTxSamplingRate(conf.txSamplingRate, txAntennaIdx);
    uhd::tune_request_t txTuneRequest(conf.txCarrierFrequency);
    usrpDevice_->set_tx_freq(txTuneRequest, txAntennaIdx);
    usrpDevice_->set_tx_gain(conf.txGain, txAntennaIdx);
    usrpDevice_->set_tx_bandwidth(conf.txAnalogFilterBw, txAntennaIdx);
}

void Usrp::setTxConfig(const TxStreamingConfig &conf) {
    assertValidTxSignal(conf.samples, MAX_SAMPLES_TX_SIGNAL,
                        rfConfig_.noTxAntennas);
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
    configureRxStreamer(rfConfig_);
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

void Usrp::resetStreamingConfigs() {
    txStreamingConfigs_.clear();
    rxStreamingConfigs_.clear();
}
void Usrp::setTxSamplingRate(const double samplingRate,
                             const size_t idxTxAntenna) {
    usrpDevice_->set_tx_rate(samplingRate, idxTxAntenna);
    double actualSamplingRate = usrpDevice_->get_tx_rate();
    assertSamplingRate(actualSamplingRate, masterClockRate_);
}
void Usrp::setRxSamplingRate(const double samplingRate,
                             const size_t idxRxAntenna) {
    usrpDevice_->set_rx_rate(samplingRate, idxRxAntenna);
    double actualSamplingRate = usrpDevice_->get_rx_rate(idxRxAntenna);
    assertSamplingRate(actualSamplingRate, masterClockRate_);
}

}  // namespace bi
