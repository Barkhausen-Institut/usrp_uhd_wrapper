#include <cmath>
#include <cstring>
#include <numeric>
#include <uhd/types/ref_vector.hpp>
#include <uhd/rfnoc/mb_controller.hpp>
#include <uhd/utils/graph_utils.hpp>

#include "usrp.hpp"

using namespace std::literals::chrono_literals;

namespace bi {

const int MAX_ANTENNAS = 4;
const int CHANNELS = 1;

using uhd::rfnoc::block_id_t;
using uhd::rfnoc::rfnoc_graph;
using uhd::rfnoc::noc_block_base;

void _showRfNoCConnections(uhd::rfnoc::rfnoc_graph::sptr graph) {
    auto edges = graph->enumerate_active_connections();
    std::cout << "Connections in graph: " << std::endl;
    for (auto& edge : edges)
        std::cout << edge.src_blockid << ":" << edge.src_port << " --> " << edge.dst_blockid << ":" << edge.dst_port << std::endl;
}

std::ostream& operator<<(std::ostream& os, const uhd::rfnoc::graph_edge_t& edge) {
    os << edge.src_blockid << ":" << edge.src_port << " --> " << edge.dst_blockid << ":" << edge.dst_port;
    return os;
}

Usrp::Usrp(const std::string& ip) :
    radioId1_("0/Radio#0"), radioId2_("0/Radio#1"), replayId_("0/Replay#0") {
    ip_ = ip;
    graph_ = rfnoc_graph::make("addr="+ip);
    //usrpDevice_ = uhd::usrp::multi_usrp::make(uhd::device_addr_t("addr=" + ip));

    graph_->get_mb_controller()->set_sync_source("external", "external");
    //usrpDevice_->set_sync_source("external", "external");

    masterClockRate_ = 245.76e6; // TODO!
    //masterClockRate_ = usrpDevice_->get_master_clock_rate();

    createRfNocBlocks();
}

Usrp::~Usrp() {
    graph_->get_mb_controller()->set_sync_source("internal", "internal");
    //usrpDevice_->set_sync_source("internal", "internal");

    if (transmitThread_.joinable()) transmitThread_.join();
    if (receiveThread_.joinable()) receiveThread_.join();
    if (setTimeToZeroNextPpsThread_.joinable())
        setTimeToZeroNextPpsThread_.join();
}

void Usrp::createRfNocBlocks() {
    radioCtrl1_ = graph_->get_block<uhd::rfnoc::radio_control>(radioId1_);
    radioCtrl2_ = graph_->get_block<uhd::rfnoc::radio_control>(radioId2_);

    replayCtrl_ = graph_->get_block<uhd::rfnoc::replay_block_control>(replayId_);
    for(int c = 0; c < MAX_ANTENNAS; c++) {
        replayCtrl_->set_play_type("sc16", c);
        replayCtrl_->set_record_type("sc16", c);
    }

    graph_->commit();
}

void Usrp::connectForUpload(){
    std::cout << "----> Connecting for UPLOAD..." << std::endl;
    disconnectAll();

    graph_->release();
    currentTxStreamer_.reset();
    uhd::stream_args_t streamArgs("fc32", "sc16");
    currentTxStreamer_ = graph_->create_tx_streamer(CHANNELS, streamArgs);

    std::cout << "Connecting TX streamer" << std::endl;
    for (int i = 0; i < CHANNELS; i++) {
        graph_->connect(currentTxStreamer_, i, replayId_, i);
    }

    graph_->commit();
    _showRfNoCConnections(graph_);
}

void Usrp::configureReplayForUpload(int numSamples) {
    size_t numBytes = numSamples * 4;
    size_t memStride = numBytes;

    for (int channel = 0; channel < CHANNELS; channel++) {
        replayCtrl_->record(channel*memStride, numBytes, channel);
    }
}

void Usrp::performUpload(const MimoSignal& txSignal) {
    if (txSignal.size() != CHANNELS)
        throw std::runtime_error("Invalid channel count!");

    const size_t numSamples = txSignal[0].size();
    configureReplayForUpload(numSamples);

    size_t totalSamplesSent = 0;
    size_t maxPacketSize = 8192;

    float timeout = 0.1;

    uhd::tx_metadata_t mdTx;
    mdTx.start_of_burst = false;
    mdTx.end_of_burst = false;
    mdTx.has_time_spec = true;
    mdTx.time_spec = graph_->get_mb_controller()->get_timekeeper(0)->get_time_now() + 0.1;

    while(totalSamplesSent < numSamples) {
        std::vector<const sample*> buffers;
        for(int txI = 0; txI < CHANNELS; txI++) {
            buffers.push_back(txSignal[txI].data() + totalSamplesSent);
        }
        size_t samplesToSend = std::min(numSamples - totalSamplesSent, maxPacketSize);
        size_t samplesSent = currentTxStreamer_->send(buffers, samplesToSend, mdTx, timeout);

        mdTx.has_time_spec = false;
        totalSamplesSent += samplesSent;

        std::cout << "upload: " << totalSamplesSent << " " << samplesSent << std::endl;
    }
    mdTx.end_of_burst = true;
    currentTxStreamer_->send("", 0, mdTx);

    uhd::async_metadata_t asyncMd;
    // loop through all messages for the ACK packet (may have underflow messages
    // in queue)
    uhd::async_metadata_t::event_code_t lastEventCode =
        uhd::async_metadata_t::EVENT_CODE_BURST_ACK;
    while (currentTxStreamer_->recv_async_msg(asyncMd, timeout)) {
        if (asyncMd.event_code != uhd::async_metadata_t::EVENT_CODE_BURST_ACK)
            lastEventCode = asyncMd.event_code;
        timeout = 0.1f;
    }

    if (lastEventCode != uhd::async_metadata_t::EVENT_CODE_BURST_ACK) {
        throw std::runtime_error("Error occoured at Tx Streamer with event code: " +
                            std::to_string(lastEventCode));
    }

    std::this_thread::sleep_for(100ms);
    for(int c = 0; c < CHANNELS; c++) {
        std::cout << "Upload Replay Fullness channel " << c << " " << replayCtrl_->get_record_fullness(c) << std::endl;
    }
}

void Usrp::connectForStreaming() {
    std::cout << "----> Connecting for STREAMING..." << std::endl;
    disconnectAll();

    graph_->release();
    for (int i = 0; i < CHANNELS; i++) {
        auto radioId = radioId1_;
        int radioChan = i;
        if (i >= 2) {
            radioId = radioId2_;
            radioChan = i - 2;
        }

        std::cout << "Connecting " << radioId << " " << radioChan << " to " << replayId_ << " " << i << std::endl;
        /*graph->connect(replayId, i, radioId, radioChan, false);
            graph->connect(radioId, radioChan, replayId, i, true);*/
        ::uhd::rfnoc::connect_through_blocks(graph_, replayId_, i, radioId, radioChan, false);
        ::uhd::rfnoc::connect_through_blocks(graph_, radioId, radioChan, replayId_, i, true);
    }

    graph_->commit();
    _showRfNoCConnections(graph_);
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

    std::this_thread::sleep_for(10ms);

    // Clear Replay block
    for(int t = 0; t < 3; t++) {
        bool needClear = false;
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

    uhd::stream_cmd_t txStreamCmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    txStreamCmd.num_samps = numTxSamples;
    txStreamCmd.stream_now = false;
    txStreamCmd.time_spec = uhd::time_spec_t(streamTime);

    uhd::stream_cmd_t rxStreamCmd = txStreamCmd;
    rxStreamCmd.num_samps = numRxSamples;
    rxStreamCmd.stream_now = false;
    std::cout << "current fpga time: " << getCurrentFpgaTime() << " stream time: " << streamTime << std::endl;
    rxStreamCmd.time_spec = uhd::time_spec_t(streamTime);

    for (int channel = 0; channel < CHANNELS; channel++) {
        auto rcp = getRadioChannelPair(channel);
        std::get<0>(rcp)->issue_stream_cmd(rxStreamCmd, std::get<1>(rcp));
        replayCtrl_->issue_stream_cmd(txStreamCmd, channel);
    }

    for(int c = 0; c < CHANNELS; c++) {
        std::cout << "Streaming Replay Fullness channel " << c << " " << replayCtrl_->get_record_fullness(c) << std::endl;
        std::cout << "Streaming Replay play pos channel " << c << " " << replayCtrl_->get_play_position(c) << std::endl;
    }
    std::this_thread::sleep_for(2000ms);
    for(int c = 0; c < CHANNELS; c++) {
        std::cout << "Streaming Replay Fullness channel " << c << " " << replayCtrl_->get_record_fullness(c) << std::endl;
        std::cout << "Streaming Replay play pos channel " << c << " " << replayCtrl_->get_play_position(c) << std::endl;
    }
}

void Usrp::connectForDownload() {
    std::cout << "----> Connecting for DOWNLOAD ..." << std::endl;
    disconnectAll();

    graph_->release();
    currentRxStreamer_.reset();
    uhd::stream_args_t streamArgs("fc32", "sc16");
    currentRxStreamer_ = graph_->create_rx_streamer(CHANNELS, streamArgs);

    for(int i = 0; i < CHANNELS; i++)
        graph_->connect(replayId_, i, currentRxStreamer_, i);
    graph_->commit();

    _showRfNoCConnections(graph_);
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

    MimoSignal result;
    result.resize(CHANNELS);
    for(int c = 0; c < CHANNELS; c++) {
        result[c].resize(numRxSamples);
    }

    uhd::stream_cmd_t streamCmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    streamCmd.num_samps = numRxSamples;
    streamCmd.stream_now = false;
    streamCmd.time_spec = graph_->get_mb_controller()->get_timekeeper(0)->get_time_now() + 0.1;

    currentRxStreamer_->issue_stream_cmd(streamCmd);
    uhd::rx_metadata_t mdRx;
    size_t totalSamplesReceived = 0;
    size_t maxPacketSize = 8192;

    while (totalSamplesReceived < numRxSamples) {
        std::vector<sample*> buffers;
        for(int c = 0; c < CHANNELS; c++)
            buffers.push_back(result[c].data() + totalSamplesReceived);
        size_t remainingSamples = numRxSamples - totalSamplesReceived;
        size_t reqSamples = std::min(remainingSamples, maxPacketSize);
        size_t numSamplesReceived = currentRxStreamer_->recv(buffers, reqSamples, mdRx, 0.1, false);

        totalSamplesReceived += numSamplesReceived;
        if (mdRx.error_code != uhd::rx_metadata_t::error_code_t::ERROR_CODE_NONE)
            throw std::runtime_error("error at Rx streamer " + mdRx.strerror());
    }

    std::cout << "Returning... " << std::endl;
    return result;
}

void Usrp::disconnectAll() {
    graph_->release();
    for (auto& edge : graph_->enumerate_active_connections()) {
        if (edge.dst_blockid.find("RxStreamer") != std::string::npos) {
            graph_->disconnect(edge.src_blockid, edge.src_port);
        }
        else if (edge.src_blockid.find("TxStreamer") != std::string::npos) {
            graph_->disconnect(edge.dst_blockid, edge.dst_port);
        }
        else {
            graph_->disconnect(edge.src_blockid, edge.src_port, edge.dst_blockid, edge.dst_port);
        }
    }

    if (currentTxStreamer_) {
        for(int i = 0; i < CHANNELS; i++)
            graph_->disconnect("TxStreamer#0", i);
        graph_->disconnect("TxStreamer#0");
        currentTxStreamer_.reset();
    }
    if (currentRxStreamer_) {
        for(int i = 0; i < CHANNELS; i++)
            graph_->disconnect("RxStreamer#0", i);
        currentRxStreamer_.reset();
    }

    graph_->commit();
    //_showRfNoCConnections(graph_);
}

RfConfig Usrp::getRfConfig() const {
    RfConfig conf;
    std::scoped_lock lock(fpgaAccessMutex_);
    conf.txCarrierFrequency = radioCtrl1_->get_tx_frequency(0);
    //conf.txCarrierFrequency = usrpDevice_->get_tx_freq(0);

    conf.txGain = radioCtrl1_->get_tx_gain(0);
    //conf.txGain = usrpDevice_->get_tx_gain(0);

    conf.txAnalogFilterBw = radioCtrl1_->get_tx_bandwidth(0);
    //conf.txAnalogFilterBw = usrpDevice_->get_tx_bandwidth(0);

    conf.txSamplingRate = masterClockRate_;  // TODO!
    //conf.txSamplingRate = usrpDevice_->get_tx_rate(0);

    conf.rxCarrierFrequency = radioCtrl1_->get_rx_frequency(0);
    //conf.rxCarrierFrequency = usrpDevice_->get_rx_freq(0);

    conf.rxGain = radioCtrl1_->get_rx_gain(0);
    //conf.rxGain = usrpDevice_->get_rx_gain(0);

    conf.rxAnalogFilterBw = radioCtrl1_->get_rx_bandwidth(0);
    //conf.rxAnalogFilterBw = usrpDevice_->get_rx_bandwidth(0);

    conf.rxSamplingRate = masterClockRate_; // TODO!
    //conf.rxSamplingRate = usrpDevice_->get_rx_rate(0);


    // TODO!
    conf.noRxAntennas = 1;
    conf.noTxAntennas = 1;
    //conf.noRxAntennas = usrpDevice_->get_rx_subdev_spec().size();
    //conf.noTxAntennas = usrpDevice_->get_tx_subdev_spec().size();
    return conf;
}

void Usrp::receive(const double baseTime, std::vector<MimoSignal> &buffers,
                   std::exception_ptr &exceptionPtr) {
    if (!rxStreamer_) configureRxStreamer(getRfConfig());
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

    // TODO! remove?
    // if (!subdevSpecSet_) {
    //     usrpDevice_->set_rx_subdev_spec(
    //         uhd::usrp::subdev_spec_t(SUBDEV_SPECS[conf.noRxAntennas - 1]), 0);
    //     usrpDevice_->set_tx_subdev_spec(
    //         uhd::usrp::subdev_spec_t(SUBDEV_SPECS[conf.noTxAntennas - 1]), 0);
    //     subdevSpecSet_ = true;
    // }
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
    return;
    if (rxStreamer_) rxStreamer_.reset();
    uhd::stream_args_t rxStreamArgs("fc32", "sc16");
    rxStreamArgs.channels = std::vector<size_t>({});
    for (int rxAntennaIdx = 0; rxAntennaIdx < conf.noRxAntennas; rxAntennaIdx++)
        rxStreamArgs.channels.push_back(rxAntennaIdx);
    rxStreamer_ = usrpDevice_->get_rx_stream(rxStreamArgs);
}

void Usrp::configureTxStreamer(const RfConfig &conf) {
    return;
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
    auto [radio, channel] = getRadioChannelPair(rxAntennaIdx);
    radio->set_rx_frequency(conf.rxCarrierFrequency, channel);
    radio->set_rx_gain(conf.rxGain, channel);
    radio->set_rx_bandwidth(conf.rxAnalogFilterBw, channel);

    // TODO! Set Sampling rate

    // setRxSamplingRate(conf.rxSamplingRate, rxAntennaIdx);
    // uhd::tune_request_t rxTuneRequest(conf.rxCarrierFrequency);
    // usrpDevice_->set_rx_freq(rxTuneRequest, rxAntennaIdx);
    // usrpDevice_->set_rx_gain(conf.rxGain, rxAntennaIdx);
    // usrpDevice_->set_rx_bandwidth(conf.rxAnalogFilterBw, rxAntennaIdx);
}

void Usrp::setRfConfigForTxAntenna(const RfConfig &conf,
                                   const size_t txAntennaIdx) {
    auto [radio, channel] = getRadioChannelPair(txAntennaIdx);
    radio->set_tx_frequency(conf.txCarrierFrequency, channel);
    radio->set_tx_gain(conf.txGain, channel);
    radio->set_tx_bandwidth(conf.txAnalogFilterBw, channel);

    // setTxSamplingRate(conf.txSamplingRate, txAntennaIdx);
    // uhd::tune_request_t txTuneRequest(conf.txCarrierFrequency);
    // usrpDevice_->set_tx_freq(txTuneRequest, txAntennaIdx);
    // usrpDevice_->set_tx_gain(conf.txGain, txAntennaIdx);
    // usrpDevice_->set_tx_bandwidth(conf.txAnalogFilterBw, txAntennaIdx);
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
    std::cout << "execute STUB!" << std::endl;

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
void Usrp::setTxSamplingRate(const double samplingRate,
                             const size_t idxTxAntenna) {
    std::cout << "STUB tx sampling rate!" << std::endl;
    return;

    usrpDevice_->set_tx_rate(samplingRate, idxTxAntenna);
    double actualSamplingRate = usrpDevice_->get_tx_rate();
    assertSamplingRate(actualSamplingRate, masterClockRate_);
}
void Usrp::setRxSamplingRate(const double samplingRate,
                             const size_t idxRxAntenna) {
    std::cout << "STUB rx sampling rate!" << std::endl;
    return;

    usrpDevice_->set_rx_rate(samplingRate, idxRxAntenna);
    double actualSamplingRate = usrpDevice_->get_rx_rate(idxRxAntenna);
    assertSamplingRate(actualSamplingRate, masterClockRate_);
}

void Usrp::waitOnThreadToJoin(std::thread &t) {
    if (t.joinable()) t.join();
}

std::string Usrp::getDeviceType() const {
    return graph_->get_mb_controller()->get_mboard_name();
    //return usrpDevice_->get_mboard_name();
}

Usrp::RadioChannelPair Usrp::getRadioChannelPair(int antenna) {
    if (antenna < 2)
        return {radioCtrl1_, antenna};
    else
        return {radioCtrl2_, antenna - 2};
}
}  // namespace bi
