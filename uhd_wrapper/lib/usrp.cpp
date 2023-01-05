#include <cmath>
#include <cstring>
#include <numeric>
#include <uhd/types/ref_vector.hpp>
#include <uhd/rfnoc/mb_controller.hpp>

#include "usrp.hpp"
#include "usrp_exception.hpp"

using namespace std::literals::chrono_literals;

namespace bi {

const int MAX_ANTENNAS = 4;
const int CHANNELS = 1;

using uhd::rfnoc::block_id_t;
using uhd::rfnoc::rfnoc_graph;
using uhd::rfnoc::noc_block_base;


Usrp::Usrp(const std::string& ip) :
    replayId_("0/Replay#0") {
    ip_ = ip;
    graph_ = rfnoc_graph::make("addr="+ip);
    bi::RfNocBlockConfig blockNames;
    blockNames.radioIds = {"0/Radio#0", "0/Radio#1"};
    blockNames.replayId = "0/Replay#0";

    fdGraph_ = std::make_shared<RfNocFullDuplexGraph>(blockNames, graph_);
    rfConfig_ = std::make_shared<RFConfiguration>(blockNames, graph_);


    createRfNocBlocks();

    // Need to perform one cycle of connections such that the radios are preinitialized
    // in order to be able to set a reasonable RF config and sample rate for the DDC/DUC
    connectForUpload();
    connectForStreaming();
    connectForDownload();
}

Usrp::~Usrp() {
    graph_->get_mb_controller()->set_sync_source("internal", "internal");

    if (transmitThread_.joinable()) transmitThread_.join();
    if (receiveThread_.joinable()) receiveThread_.join();
    if (setTimeToZeroNextPpsThread_.joinable())
        setTimeToZeroNextPpsThread_.join();
}

void Usrp::createRfNocBlocks() {
    using uhd::rfnoc::block_id_t;

    replayCtrl_ = graph_->get_block<uhd::rfnoc::replay_block_control>(replayId_);

    graph_->commit();
}

void Usrp::connectForUpload(){
    fdGraph_->connectForUpload(CHANNELS);
}

void Usrp::configureReplayForUpload(int numSamples) {
    size_t numBytes = numSamples * 4;
    size_t memStride = numBytes;

    for (int channel = 0; channel < CHANNELS; channel++) {
        replayCtrl_->record(channel*memStride, numBytes, channel);
    }

    clearReplayBlockRecorder();
}

void Usrp::performUpload(const MimoSignal& txSignal) {
    const size_t numSamples = txSignal[0].size();
    configureReplayForUpload(numSamples);

    fdGraph_->upload(txSignal);
}

void Usrp::connectForStreaming() {
    fdGraph_->connectForStreaming(CHANNELS, CHANNELS);
}

void Usrp::configureReplayForStreaming(size_t numTxSamples, size_t numRxSamples) {
    size_t memSize = replayCtrl_->get_mem_size();
    size_t halfMem = memSize / 2;

    size_t numTxBytes = numTxSamples * 4;
    size_t txMemStride = numTxBytes;
    size_t numRxBytes = numRxSamples * 4;
    size_t rxMemStride = numRxBytes;

    for (int channel = 0; channel < CHANNELS; channel++) {
        if (numRxBytes > 0)
            replayCtrl_->record(halfMem + channel*rxMemStride, numRxBytes, channel);
        if (numTxBytes > 0)
            replayCtrl_->config_play(channel*txMemStride, numTxBytes, channel);
    }

    clearReplayBlockRecorder();
}

void Usrp::clearReplayBlockRecorder() {
    std::this_thread::sleep_for(10ms);

    bool needClear = false;
    for(int t = 0; t < 3; t++) {
        needClear = false;
        for(int c = 0; c < CHANNELS; c++)
            needClear |= (replayCtrl_->get_record_fullness(c) > 0);

        if (!needClear)
            break;

        std::cout << "Trying to clear the buffer" << std::endl;
        for(int c = 0; c < CHANNELS; c++)
            replayCtrl_->record_restart(c);
    }
    if (needClear)
        throw UsrpException("Cannot clear the record buffer!");
}

void Usrp::performStreaming(double streamTime, size_t numTxSamples, size_t numRxSamples) {
    configureReplayForStreaming(numTxSamples, numRxSamples);

    // We need to make sure that the sample rate is set again, because when disconnecting
    // the DDC/DUC blocks it might happen that the rate is reset. Therefore, to be on the safe
    // side, we apply the sample rate again.
    rfConfig_->renewSampleRateSettings();

    int rxDecimFactor = rfConfig_->getRxDecimationRatio();
    std::cout << "RX dec factor: " << rxDecimFactor << std::endl;

    // We need to multiply with the rx decim factor because we
    // instruct the radio to create a given amount of samples, which
    // are subsequentcy decimated by the DDC (hence the radio needs to
    // produce more decim times more samples to eventually yield the
    // correct amount of samples.  On the TX side, we instruct the
    // replay block to create a given amount of samples, which is
    // equal to the amount of baseband samples. Hence, no scaling is
    // needed.
    fdGraph_->stream(streamTime, numTxSamples, numRxSamples * rxDecimFactor);
}

void Usrp::connectForDownload() {
    fdGraph_->connectForDownload(CHANNELS);
    return;
}

void Usrp::configureReplayForDownload(size_t numRxSamples) {
    size_t memSize = replayCtrl_->get_mem_size();
    size_t halfMem = memSize / 2;
    size_t numBytes = numRxSamples * 4;
    size_t memStride = numBytes;

    for (int channel = 0; channel < CHANNELS; channel++) {
        replayCtrl_->config_play(halfMem + channel*memStride, numBytes, channel);
    }
}

MimoSignal Usrp::performDownload(size_t numRxSamples) {
    configureReplayForDownload(numRxSamples);
    return fdGraph_->download(numRxSamples);
}

RfConfig Usrp::getRfConfig() const {
    return rfConfig_->readFromGraph();
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
}

void Usrp::setRfConfig(const RfConfig &conf) {
    rfConfig_->setRfConfig(conf);
}


void Usrp::setTxConfig(const TxStreamingConfig &conf) {
    assertValidTxSignal(conf.samples, MAX_SAMPLES_TX_SIGNAL, rfConfig_->getNumTxAntennas());
    if (txStreamingConfigs_.size() > 0)
        assertValidTxStreamingConfig(txStreamingConfigs_.back(), conf,
                                     GUARD_OFFSET_S_, rfConfig_->getTxSamplingRate());
    txStreamingConfigs_.push_back(conf);
}

void Usrp::setRxConfig(const RxStreamingConfig &conf) {
    if (rxStreamingConfigs_.size() > 0)
        assertValidRxStreamingConfig(rxStreamingConfigs_.back(), conf,
                                     GUARD_OFFSET_S_, rfConfig_->getRxSamplingRate());
    rxStreamingConfigs_.push_back(conf);
}

void Usrp::setTimeToZeroNextPps() {
    // join previous thread to make sure it has properly ended. This is also
    // necessary to use op= below (it'll std::terminate() if not joined
    // before)
    waitOnThreadToJoin(setTimeToZeroNextPpsThread_);

    setTimeToZeroNextPpsThread_ =
        std::thread(&Usrp::setTimeToZeroNextPpsThreadFunction, this);
}

void Usrp::setTimeToZeroNextPpsThreadFunction() {
    std::scoped_lock lock(fpgaAccessMutex_);

    auto keeper = graph_->get_mb_controller()->get_timekeeper(0);
    keeper->set_time_next_pps(uhd::time_spec_t(0.0));

    // wait for next pps
    const uhd::time_spec_t lastPpsTime = keeper->get_time_last_pps();
    while (lastPpsTime == keeper->get_time_last_pps()) {
        // TODO! Busy waiting!
    }
    //rxStreamer_.reset();  // cf. issue https://github.com/EttusResearch/uhd/issues/593
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
    waitOnThreadToJoin(setTimeToZeroNextPpsThread_);

    return graph_->get_mb_controller()->get_timekeeper(0)->get_time_now().get_real_secs();
    //return usrpDevice_->get_time_now().get_real_secs();
}

void Usrp::execute(const double baseTime) {
    if (txStreamingConfigs_.size() > 1)
        throw UsrpException("Only 1 TX Config currently allowed!");
    if (rxStreamingConfigs_.size() > 1)
        throw UsrpException("Only 1 RX Config currently allowed!");

    connectForUpload();
    performUpload(txStreamingConfigs_[0].samples);

    connectForStreaming();
    performStreaming(txStreamingConfigs_[0].sendTimeOffset + baseTime + 1,
                     txStreamingConfigs_[0].samples[0].size(),
                     rxStreamingConfigs_[0].noSamples);

    connectForDownload();

    receivedSamples_.clear();
    receivedSamples_.push_back(performDownload(rxStreamingConfigs_[0].noSamples));

    return;

    waitOnThreadToJoin(setTimeToZeroNextPpsThread_);
    waitOnThreadToJoin(transmitThread_);
    waitOnThreadToJoin(receiveThread_);
    receivedSamples_ = {{{}}};

    if (txStreamingConfigs_.size() > 0)
        transmitThread_ = std::thread(&Usrp::transmit, this, baseTime,
                                      std::ref(transmitThreadException_));
    if (rxStreamingConfigs_.size() > 0)
        receiveThread_ = std::thread(&Usrp::receive, this, baseTime,
                                     std::ref(receivedSamples_),
                                     std::ref(receiveThreadException_));
}

std::vector<MimoSignal> Usrp::collect() {
    std::cout << "collect STUB!" << std::endl;

    return receivedSamples_;

    waitOnThreadToJoin(transmitThread_);
    waitOnThreadToJoin(receiveThread_);
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

void Usrp::waitOnThreadToJoin(std::thread &t) {
    if (t.joinable()) t.join();
}

std::string Usrp::getDeviceType() const {
    return graph_->get_mb_controller()->get_mboard_name();
}

}  // namespace bi
