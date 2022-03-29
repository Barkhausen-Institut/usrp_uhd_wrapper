#include "usrp.hpp"

namespace bi {

void Usrp::transmit() {
    // assume one txStreamConfig for the moment....
    TxStreamingConfig txStreamingConfig = txStreamingConfigs_[0];
    size_t noPackages =
        txStreamingConfig.samples[0].size() / SAMPLES_PER_BUFFER;
    std::vector<samples_vec> channelBuffers(1, samples_vec(2000));
    std::vector<sample*> channelBuffersPtrs = {&channelBuffers[0].front()};

    std::vector<std::vector<samples_vec>> packets(
        static_cast<size_t>(noPackages));

    uhd::tx_metadata_t mdTx;
    mdTx.start_of_burst = true;
    mdTx.end_of_burst = false;
    mdTx.has_time_spec = true;

    // prebuffer all the samples for speed purposes
    int sampleIdx = 0;
    for (size_t packageIdx = 0; packageIdx < noPackages; packageIdx++) {
        for (size_t bufferSample = 0; bufferSample < SAMPLES_PER_BUFFER;
             bufferSample++) {
            for (size_t channelIdx = 0; channelIdx < 1; channelIdx++) {
                channelBuffers[channelIdx][bufferSample] =
                    txStreamingConfig.samples[channelIdx][sampleIdx];
            }
            sampleIdx++;
        }
        packets[packageIdx] = channelBuffers;
    }

    mdTx.time_spec = uhd::time_spec_t(txStreamingConfig.sendTimeOffset);

    for (size_t packageIdx = 0; packageIdx < noPackages; packageIdx++) {
        channelBuffersPtrs[0] = &packets[0][0].front();
        size_t numTxSamples = txStreamer_->send(channelBuffersPtrs,
                                                SAMPLES_PER_BUFFER, mdTx, 0.1f);
        (void)numTxSamples;
        mdTx.start_of_burst = false;
    }
    mdTx.end_of_burst = true;
    txStreamer_->send("", 0, mdTx);
}

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

std::vector<samples_vec> Usrp::execute() {
    std::thread transmitThread(&Usrp::transmit, this);
    transmitThread.join();
    std::this_thread::sleep_for(std::chrono::seconds(
        static_cast<int>(txStreamingConfigs_[0].sendTimeOffset) + 10));
    return {{}};
}
std::shared_ptr<UsrpInterface> createUsrp(std::string ip) {
    return std::make_shared<Usrp>(ip);
}
}  // namespace bi
