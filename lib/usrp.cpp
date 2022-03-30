#include <math.h>
#include "usrp.hpp"

namespace bi {

void Usrp::transmit() {
    // assume one txStreamConfig for the moment....
    TxStreamingConfig txStreamingConfig = txStreamingConfigs_[0];

    // create buffers etc
    size_t noPackages =
        std::ceil(txStreamingConfig.samples[0].size() / SAMPLES_PER_BUFFER);
    std::vector<samples_vec> channelBuffers(1, samples_vec(SAMPLES_PER_BUFFER));
    std::vector<sample*> channelBuffersPtrs = {&channelBuffers[0].front()};

    // specifiy on specifications of how to stream the command
    uhd::tx_metadata_t mdTx;
    mdTx.start_of_burst = true;
    mdTx.end_of_burst = false;
    mdTx.has_time_spec = true;

    mdTx.time_spec = uhd::time_spec_t(txStreamingConfig.sendTimeOffset);

    int sampleIdx = 0;
    for (size_t packageIdx = 0; packageIdx < noPackages; packageIdx++) {
        // buffer
        for (size_t bufferSampleIdx = 0; bufferSampleIdx < SAMPLES_PER_BUFFER;
             bufferSampleIdx++) {
            channelBuffers[0][bufferSampleIdx] =
                txStreamingConfig.samples[0][sampleIdx];
            sampleIdx++;
        }
        size_t numTxSamples = txStreamer_->send(channelBuffersPtrs,
                                                SAMPLES_PER_BUFFER, mdTx, 0.1f);
        (void)numTxSamples;  // avoid error on unused variable
        mdTx.start_of_burst = false;
    }
    mdTx.end_of_burst = true;
    txStreamer_->send("", 0, mdTx);
    // we need to introduce this sleep to ensure that the samples have already
    // been sent since the buffering is non-blocking inside the thread. If we
    // close the the outer scope before the samples are actually sent, they will
    // not be sent any more out of the FPGA.
    std::this_thread::sleep_for(std::chrono::milliseconds(
        static_cast<int>(1000 * txStreamingConfigs_[0].sendTimeOffset) + 300));
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

    ppsSetToZero_ = true;
}

uint64_t Usrp::getCurrentTime() {
    using namespace std::chrono;
    uint64_t msSinceEpoch =
        duration_cast<milliseconds>(system_clock::now().time_since_epoch())
            .count();
    return msSinceEpoch;
}

std::vector<samples_vec> Usrp::execute() {
    std::vector<samples_vec> receivedSamples = {{}};
    if (ppsSetToZero_) {
        std::thread transmitThread(&Usrp::transmit, this);
        transmitThread.join();
    }
    return receivedSamples;
}
std::shared_ptr<UsrpInterface> createUsrp(std::string ip) {
    return std::make_shared<Usrp>(ip);
}
}  // namespace bi
