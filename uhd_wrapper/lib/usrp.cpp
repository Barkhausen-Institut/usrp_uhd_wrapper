#include <chrono>
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


Usrp::Usrp(const std::string& ip)  {
    ip_ = ip;
    graph_ = rfnoc_graph::make("addr="+ip);
    RfNocBlockConfig blockNames = RfNocBlockConfig::defaultNames();

    fdGraph_ = std::make_shared<RfNocFullDuplexGraph>(blockNames, graph_);
    rfConfig_ = std::make_shared<RFConfiguration>(blockNames, graph_);

    createRfNocBlocks();

    // Need to perform one cycle of connections such that the radios are preinitialized
    // in order to be able to set a reasonable RF config and sample rate for the DDC/DUC
    fdGraph_->connectForUpload(MAX_ANTENNAS);
    fdGraph_->connectForStreaming(MAX_ANTENNAS, MAX_ANTENNAS);
    fdGraph_->connectForDownload(MAX_ANTENNAS);
}

Usrp::~Usrp() {
    graph_->get_mb_controller()->set_sync_source("internal", "internal");

    if (transmitThread_.joinable()) transmitThread_.join();
    if (receiveThread_.joinable()) receiveThread_.join();
    if (setTimeToZeroNextPpsThread_.joinable())
        setTimeToZeroNextPpsThread_.join();
}

void Usrp::createRfNocBlocks() {

    auto replayCtrl = fdGraph_->getReplayControl();
    replayConfig_ = std::make_shared<ReplayBlockConfig>(
            std::make_shared<ReplayBlockWrapper>(replayCtrl));

    graph_->commit();
}

void Usrp::configureReplayForUpload(int numSamples) {
    /*size_t numBytes = numSamples * 4;
    size_t memStride = numBytes;

    for (int channel = 0; channel < CHANNELS; channel++) {
        replayCtrl_->record(channel*memStride, numBytes, channel);
        }*/

    replayConfig_->configUpload(numSamples);

    //clearReplayBlockRecorder();
}

void Usrp::performUpload() {
    fdGraph_->connectForUpload(rfConfig_->getNumTxAntennas());
    for(const auto& config : txStreamingConfigs_) {
        const auto& txSignal = config.samples;
        const size_t numSamples = txSignal[0].size();
        configureReplayForUpload(numSamples);

        fdGraph_->upload(txSignal);
    }
}

void Usrp::configureReplayForStreaming(size_t numTxSamples, size_t numRxSamples) {
    replayConfig_->configTransmit(numTxSamples);
    replayConfig_->configReceive(numRxSamples);
}

void Usrp::performStreaming(double baseTime) {
    fdGraph_->connectForStreaming(rfConfig_->getNumTxAntennas(),
                                  rfConfig_->getNumRxAntennas());

    // We need to make sure that the sample rate is set again, because when disconnecting
    // the DDC/DUC blocks it might happen that the rate is reset. Therefore, to be on the safe
    // side, we apply the sample rate again.
    rfConfig_->renewSampleRateSettings();

    transmitThread_ = std::thread([this,baseTime]() {
        for(const auto& config : txStreamingConfigs_) {
            double streamTime = config.sendTimeOffset + baseTime;
            size_t numTxSamples = config.samples[0].size();
            replayConfig_->configTransmit(numTxSamples);
            fdGraph_->transmit(streamTime, numTxSamples);
        }
    });

    receiveThread_ = std::thread([this,baseTime]() {
        int rxDecimFactor = rfConfig_->getRxDecimationRatio();
        std::cout << "RX dec factor: " << rxDecimFactor << std::endl;

        for(const auto& config: rxStreamingConfigs_) {
            double streamTime = config.receiveTimeOffset + baseTime;
            size_t numRxSamples = config.noSamples;
            replayConfig_->configReceive(numRxSamples);

            // We need to multiply with the rx decim factor because we
            // instruct the radio to create a given amount of samples, which
            // are subsequentcy decimated by the DDC (hence the radio needs to
            // produce more decim times more samples to eventually yield the
            // correct amount of samples.  On the TX side, we instruct the
            // replay block to create a given amount of samples, which is
            // equal to the amount of baseband samples. Hence, no scaling is
            // needed.
            fdGraph_->receive(streamTime, numRxSamples*rxDecimFactor);
        }
    });


    //fdGraph_->stream(streamTime, numTxSamples, numRxSamples * rxDecimFactor);
}

void Usrp::configureReplayForDownload(size_t numRxSamples) {
    replayConfig_->configDownload(numRxSamples);
}

void Usrp::performDownload() {
    receivedSamples_.clear();
    fdGraph_->connectForDownload(rfConfig_->getNumRxAntennas());

    for(const auto& config: rxStreamingConfigs_) {
        configureReplayForDownload(config.noSamples);
        receivedSamples_.push_back(fdGraph_->download(config.noSamples));
    }
}

RfConfig Usrp::getRfConfig() const {
    return rfConfig_->readFromGraph();
}

double Usrp::getMasterClockRate() const {
    return rfConfig_->getMasterClockRate();
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
    replayConfig_->setAntennaCount(conf.noTxAntennas, conf.noRxAntennas);
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
}

void Usrp::execute(const double baseTime) {
    if (txStreamingConfigs_.size() > 1)
        throw UsrpException("Only 1 TX Config currently allowed!");
    if (rxStreamingConfigs_.size() > 1)
        throw UsrpException("Only 1 RX Config currently allowed!");

    performUpload();

    performStreaming(baseTime);

    // performDownload();

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

    waitOnThreadToJoin(transmitThread_);
    waitOnThreadToJoin(receiveThread_);
    performDownload();

    resetStreamingConfigs();

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
