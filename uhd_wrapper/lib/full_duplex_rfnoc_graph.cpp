#include "full_duplex_rfnoc_graph.hpp"

#include <chrono>
#include <uhd/utils/graph_utils.hpp>

#include "usrp_exception.hpp"

namespace bi {

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

RfNocFullDuplexGraph::RfNocFullDuplexGraph(const RfNocBlockConfig& config,
                                           uhd::rfnoc::rfnoc_graph::sptr graph,
                                           const StreamMapper& streamMapper)
    : RfNocBlocks(config, graph), streamMapper_(streamMapper) {

    for(size_t c = 0; c < getNumAntennas(); c++) {
        replayCtrl_->set_play_type("sc16", c);
        replayCtrl_->set_record_type("sc16", c);
    }
    setSyncSource("internal");
}

uhd::rfnoc::replay_block_control::sptr RfNocFullDuplexGraph::getReplayControl() {
    return replayCtrl_;
}

void RfNocFullDuplexGraph::setSyncSource(const std::string &type){
    if (type != "internal" && type != "external")
        throw UsrpException("Invalid sync source " + type);

    if (currentSyncSource_ == type)
        return;
    graph_->get_mb_controller()->set_sync_source(type, type);
    currentSyncSource_ = type;
}

uhd::tx_streamer::sptr RfNocFullDuplexGraph::connectForUpload(size_t numTxStreams) {
    disconnectAll();

    numTxStreams_ = numTxStreams;

    graph_->release();
    currentTxStreamer_.reset();
    uhd::stream_args_t streamArgs("fc32", "sc16");
    currentTxStreamer_ = graph_->create_tx_streamer(numTxStreams_, streamArgs);

    for (size_t i = 0; i < numTxStreams_; i++) {
        graph_->connect(currentTxStreamer_, i,
                        replayCtrl_->get_block_id(), i);
    }

    graph_->commit();

    return currentTxStreamer_;
    // _showRfNoCConnections(graph_);
}

void RfNocFullDuplexGraph::upload(const MimoSignal& txSignal) {
    if (txSignal.size() != numTxStreams_)
        throw std::runtime_error("Invalid channel count!");

    const size_t numSamples = txSignal[0].size();
    //configureReplayForUpload(numSamples);


    float timeout = 0.1;

    uhd::tx_metadata_t mdTx;
    mdTx.start_of_burst = true;
    mdTx.end_of_burst = false;
    mdTx.has_time_spec = false;
    // After some tests, it seems that the timing is not considered in
    // UHD. We don't care because anyway we are just streaming into a
    // memory of the replay block.
    // mdTx.time_spec = getCurrentFpgaTime() + 0.1;

    size_t totalSamplesSent = 0;
    while(totalSamplesSent < numSamples) {
        std::vector<const sample*> buffers;
        for(size_t txI = 0; txI < numTxStreams_; txI++) {
            buffers.push_back(txSignal[txI].data() + totalSamplesSent);
        }
        size_t samplesToSend = std::min(numSamples - totalSamplesSent, PACKET_SIZE);
        size_t samplesSent = currentTxStreamer_->send(buffers, samplesToSend, mdTx, timeout);

        mdTx.has_time_spec = false;
        mdTx.start_of_burst = false;
        totalSamplesSent += samplesSent;
    }
    mdTx.end_of_burst = true;
    currentTxStreamer_->send("", 0, mdTx);

    uhd::async_metadata_t asyncMd;
    // loop through all messages for the ACK packet (may have underflow messages
    // in queue)
    // However, recent tests show that no messages are received at all by the streamer.
    uhd::async_metadata_t::event_code_t lastEventCode =
        uhd::async_metadata_t::EVENT_CODE_BURST_ACK;
    timeout = 0.02f;
    while (currentTxStreamer_->recv_async_msg(asyncMd, timeout)) {
        if (asyncMd.event_code != uhd::async_metadata_t::EVENT_CODE_BURST_ACK)
            lastEventCode = asyncMd.event_code;
        timeout = 0.01f;
    }

    if (lastEventCode != uhd::async_metadata_t::EVENT_CODE_BURST_ACK) {
        throw std::runtime_error("Error occoured at Tx Streamer with event code: " +
                            std::to_string(lastEventCode));
    }

    for(size_t c = 0; c < numTxStreams_; c++) {
        std::cout << "Upload Replay Fullness channel " << c << " " << replayCtrl_->get_record_fullness(c) << std::endl;
    }
}
void RfNocFullDuplexGraph::connectForStreaming(size_t numTxStreams, size_t numRxStreams) {
    if (numTxStreams != numTxStreams_)
        throw UsrpException("Streaming with wrong number of TX antennas! " +
        std::to_string(numTxStreams) + " " + std::to_string(numTxStreams_));
    numRxStreams_ = numRxStreams;

    disconnectAll();

    using uhd::rfnoc::block_id_t;

    graph_->release();
    for (size_t i = 0; i < numTxStreams; i++) {

        uint antIdx = streamMapper_.mapTxStreamToAntenna(i);
        auto [radio, radioChan] = getRadioChannelPair(antIdx);
        uhd::rfnoc::connect_through_blocks(graph_,
                                            replayCtrl_->get_block_id(), i,
                                            radio->get_block_id(), radioChan, false);
    }

    for (size_t i = 0; i < numRxStreams; i++) {
        uint antIdx = streamMapper_.mapRxStreamToAntenna(i);
        auto [radio, radioChan] = getRadioChannelPair(antIdx);
        uhd::rfnoc::connect_through_blocks(graph_,
                                            radio->get_block_id(), radioChan,
                                            replayCtrl_->get_block_id(), i, true);
    }

    graph_->commit();
    // _showRfNoCConnections(graph_);
}

void RfNocFullDuplexGraph::transmit(double streamTime, size_t numTxSamples) {
    uhd::stream_cmd_t txStreamCmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    txStreamCmd.num_samps = numTxSamples;
    txStreamCmd.stream_now = false;
    txStreamCmd.time_spec = uhd::time_spec_t(streamTime);

    if (streamTime < getCurrentFpgaTime() + 0.02)
        throw UsrpException("Target stream time is too close. Consider increasing system.baseTimeOffset (streamTime: )"
                            + std::to_string(streamTime) + " currentTime: " + std::to_string(getCurrentFpgaTime()));

    {
        std::lock_guard<std::recursive_mutex> lock(fpgaAccessMutex_);
        for (size_t stream = 0; stream < numTxStreams_; stream++) {
            replayCtrl_->issue_stream_cmd(txStreamCmd, stream);
        }
    }

    uhd::async_metadata_t asyncMd;
    double timeout = streamTime - getCurrentFpgaTime() + 0.1;
    uhd::async_metadata_t::event_code_t lastEventCode = uhd::async_metadata_t::EVENT_CODE_BURST_ACK;
    while (replayCtrl_->get_play_async_metadata(asyncMd, timeout)) {
        if (asyncMd.event_code != uhd::async_metadata_t::EVENT_CODE_BURST_ACK)
            lastEventCode = asyncMd.event_code;
        timeout = 0.02;
    }
    if (lastEventCode != uhd::async_metadata_t::EVENT_CODE_BURST_ACK)
        throw UsrpException("Error occured at data replaying with event code: "
                        + std::to_string(lastEventCode));

    std::lock_guard<std::recursive_mutex> lock(fpgaAccessMutex_);
    // TOOD! Factor out into separate function or class
    for(size_t c = 0; c < numTxStreams_; c++) {
        std::cout << "Streaming Replay play pos channel " << c << " " << replayCtrl_->get_play_position(c) << std::endl;
    }
}

void RfNocFullDuplexGraph::receive(double streamTime, size_t numRxSamples) {
    if (numRxSamples == 0)
        return;


    uhd::stream_cmd_t rxStreamCmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    rxStreamCmd.num_samps = numRxSamples;
    rxStreamCmd.stream_now = false;
    rxStreamCmd.time_spec = uhd::time_spec_t(streamTime);

    if (streamTime < getCurrentFpgaTime() + 0.02)
        throw UsrpException("Target stream time is too close. Consider increasing system.baseTimeOffset (streamTime: )"
                            + std::to_string(streamTime) + " currentTime: " + std::to_string(getCurrentFpgaTime()));

    {
        std::lock_guard<std::recursive_mutex> lock(fpgaAccessMutex_);
        for (size_t stream = 0; stream < numRxStreams_; stream++) {
            // Need to map from the stream to the radio channel (i.e.
            // antenna idx) because the stream command is issued on the
            // transmitter side of the graph edge, which is the radio in the
            // Rx case, but the replay block in the Tx case.
            int antIdx = streamMapper_.mapRxStreamToAntenna(stream);
            auto [radio, radioChan] = getRadioChannelPair(antIdx);
            radio->issue_stream_cmd(rxStreamCmd, radioChan);
        }
    }

    uhd::rx_metadata_t asyncMd;
    double timeout = streamTime - getCurrentFpgaTime() + 0.1;
    while (replayCtrl_->get_record_async_metadata(asyncMd, timeout)) {
        if (asyncMd.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE)
            throw UsrpException("Error at recording: " + asyncMd.strerror());
        timeout = 0.02;
    }

    std::lock_guard<std::recursive_mutex> lock(fpgaAccessMutex_);
    for(size_t c = 0; c < numRxStreams_; c++) {
        std::cout << "Streaming Replay Fullness channel " << c << " " << replayCtrl_->get_record_fullness(c) << std::endl;
    }
}


uhd::rx_streamer::sptr RfNocFullDuplexGraph::connectForDownload(size_t numRxStreams) {
    if (numRxStreams != numRxStreams_)
        throw UsrpException("Downloading with wrong number of RX antennas!");

    using uhd::rfnoc::block_id_t;
    disconnectAll();

    graph_->release();
    currentRxStreamer_.reset();
    uhd::stream_args_t streamArgs("fc32", "sc16");
    currentRxStreamer_ = graph_->create_rx_streamer(numRxStreams_, streamArgs);

    for(size_t i = 0; i < numRxStreams; i++)
        graph_->connect(block_id_t(blockNames_.replayId), i, currentRxStreamer_, i);
    graph_->commit();

    numRxStreams_ = numRxStreams;

    return currentRxStreamer_;

    //_showRfNoCConnections(graph_);
}

MimoSignal RfNocFullDuplexGraph::download(size_t numRxSamples) {
    MimoSignal result;
    result.resize(numRxStreams_);
    for(size_t c = 0; c < numRxStreams_; c++)
        result[c].resize(numRxSamples);
    if (numRxSamples == 0)
        return result;

    uhd::stream_cmd_t streamCmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    streamCmd.num_samps = numRxSamples;
    streamCmd.stream_now = false;
    streamCmd.time_spec = getCurrentFpgaTime() + 0.1;

    currentRxStreamer_->issue_stream_cmd(streamCmd);

    uhd::rx_metadata_t mdRx;
    size_t totalSamplesReceived = 0;

    while (totalSamplesReceived < numRxSamples) {
        std::vector<sample*> buffers;
        for(size_t c = 0; c < numRxStreams_; c++)
            buffers.push_back(result[c].data() + totalSamplesReceived);
        size_t remainingSamples = numRxSamples - totalSamplesReceived;
        size_t reqSamples = std::min(remainingSamples, PACKET_SIZE);
        size_t numSamplesReceived = currentRxStreamer_->recv(buffers, reqSamples, mdRx, 0.1, false);
        // std::this_thread::sleep_for(std::chrono::milliseconds(10));

        totalSamplesReceived += numSamplesReceived;
        if (mdRx.error_code != uhd::rx_metadata_t::error_code_t::ERROR_CODE_NONE)
            throw std::runtime_error("error at Rx streamer " + mdRx.strerror());
    }
    if (!mdRx.end_of_burst)
        throw UsrpException("I did not receive an end_of_burst.");

    return result;
}

void RfNocFullDuplexGraph::disconnectAll() {
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
        for(size_t i = 0; i < numTxStreams_; i++)
            graph_->disconnect("TxStreamer#0", i);
        graph_->disconnect("TxStreamer#0");
        currentTxStreamer_.reset();
    }
    if (currentRxStreamer_) {
        for(size_t i = 0; i < numRxStreams_; i++)
            graph_->disconnect("RxStreamer#0", i);
        currentRxStreamer_.reset();
    }

    graph_->commit();
}

}
