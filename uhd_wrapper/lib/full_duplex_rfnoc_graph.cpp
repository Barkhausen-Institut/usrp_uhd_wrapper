#include "full_duplex_rfnoc_graph.hpp"

#include <uhd/utils/graph_utils.hpp>

#include "usrp_exception.hpp"

namespace bi {

const int CHANNELS=1;

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

RfNocFullDuplexGraph::RfNocFullDuplexGraph(uhd::rfnoc::rfnoc_graph::sptr graph, const RfNocBlockConfig& config)
    : graph_(graph) {

    createRfNocBlocks(config);
}

void RfNocFullDuplexGraph::createRfNocBlocks(const RfNocBlockConfig& config) {
    using uhd::rfnoc::block_id_t, uhd::rfnoc::radio_control, uhd::rfnoc::replay_block_control;
    blockNames_ = config;

    radioCtrl1_ = graph_->get_block<radio_control>(block_id_t(config.radioIds[0]));
    radioCtrl2_ = graph_->get_block<radio_control>(block_id_t(config.radioIds[1]));

    replayCtrl_ = graph_->get_block<replay_block_control>(block_id_t(config.replayId));
}

double RfNocFullDuplexGraph::getCurrentFpgaTime() {
    return graph_->get_mb_controller()->get_timekeeper(0)->get_time_now().get_real_secs();
}

uhd::tx_streamer::sptr RfNocFullDuplexGraph::connectForUpload(size_t numTxAntennas) {
    disconnectAll();

    graph_->release();
    currentTxStreamer_.reset();
    uhd::stream_args_t streamArgs("fc32", "sc16");
    currentTxStreamer_ = graph_->create_tx_streamer(numTxAntennas, streamArgs);

    for (size_t i = 0; i < numTxAntennas; i++)
        graph_->connect(currentTxStreamer_, i,
                        uhd::rfnoc::block_id_t(blockNames_.replayId), i);


    graph_->commit();

    numTxAntennas_ = numTxAntennas;

    return currentTxStreamer_;
    // _showRfNoCConnections(graph_);
}

void RfNocFullDuplexGraph::upload(const MimoSignal& txSignal) {
    if (txSignal.size() != numTxAntennas_)
        throw std::runtime_error("Invalid channel count!");

    const size_t numSamples = txSignal[0].size();
    //configureReplayForUpload(numSamples);


    float timeout = 0.1;

    uhd::tx_metadata_t mdTx;
    mdTx.start_of_burst = false;
    mdTx.end_of_burst = false;
    mdTx.has_time_spec = true;
    mdTx.time_spec = getCurrentFpgaTime() + 0.1;

    size_t totalSamplesSent = 0;
    while(totalSamplesSent < numSamples) {
        std::vector<const sample*> buffers;
        for(int txI = 0; txI < CHANNELS; txI++) {
            buffers.push_back(txSignal[txI].data() + totalSamplesSent);
        }
        size_t samplesToSend = std::min(numSamples - totalSamplesSent, PACKET_SIZE);
        size_t samplesSent = currentTxStreamer_->send(buffers, samplesToSend, mdTx, timeout);

        mdTx.has_time_spec = false;
        totalSamplesSent += samplesSent;
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
void RfNocFullDuplexGraph::connectForStreaming(size_t numTxAntennas, size_t numRxAntennas) {
    if (numTxAntennas != numTxAntennas_)
        throw UsrpException("Streaming with wrong number of TX antennas! " +
        std::to_string(numTxAntennas) + " " + std::to_string(numTxAntennas_));
    numRxAntennas_ = numRxAntennas;

    if (numTxAntennas != numRxAntennas)
        throw UsrpException("Currently, ony equal nTX and nRX supported!");

    disconnectAll();

    using uhd::rfnoc::block_id_t;

    graph_->release();
    for (size_t i = 0; i < numTxAntennas; i++) {
        std::string radioId = blockNames_.radioIds[0];
        int radioChan = i;
        if (i >= 2) {
            radioId = blockNames_.radioIds[1];
            radioChan = i - 2;
        }

        uhd::rfnoc::connect_through_blocks(graph_,
                                           block_id_t(blockNames_.replayId), i,
                                           block_id_t(radioId), radioChan, false);
        uhd::rfnoc::connect_through_blocks(graph_,
                                           block_id_t(radioId), radioChan,
                                           block_id_t(blockNames_.replayId), i, true);
    }

    graph_->commit();
    // _showRfNoCConnections(graph_);
}

void RfNocFullDuplexGraph::stream(double streamTime, size_t numTxSamples, size_t numRxSamples) {

    uhd::stream_cmd_t txStreamCmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    txStreamCmd.num_samps = numTxSamples;
    txStreamCmd.stream_now = false;
    txStreamCmd.time_spec = uhd::time_spec_t(streamTime);

    uhd::stream_cmd_t rxStreamCmd(uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
    rxStreamCmd.num_samps = numRxSamples;
    rxStreamCmd.stream_now = false;
    rxStreamCmd.time_spec = uhd::time_spec_t(streamTime);

    for (int channel = 0; channel < CHANNELS; channel++) {
        auto [radio, radioChan] = getRadioChannelPair(channel);
        radio->issue_stream_cmd(rxStreamCmd, radioChan);
        replayCtrl_->issue_stream_cmd(txStreamCmd, channel);
    }

    uhd::async_metadata_t asyncMd;
    double timeout = streamTime - getCurrentFpgaTime() + 0.1;
    uhd::async_metadata_t::event_code_t lastEventCode = uhd::async_metadata_t::EVENT_CODE_BURST_ACK;
    while (replayCtrl_->get_play_async_metadata(asyncMd, timeout)) {
        if (asyncMd.event_code != uhd::async_metadata_t::EVENT_CODE_BURST_ACK)
            lastEventCode = asyncMd.event_code;
        timeout = 0.1;
    }
    if (lastEventCode != uhd::async_metadata_t::EVENT_CODE_BURST_ACK)
        throw UsrpException("Error occured at data replaying with event code: "
                        + std::to_string(lastEventCode));

    // TOOD! Factor out into separate function or class
    for(int c = 0; c < CHANNELS; c++) {
        std::cout << "Streaming Replay Fullness channel " << c << " " << replayCtrl_->get_record_fullness(c) << std::endl;
        std::cout << "Streaming Replay play pos channel " << c << " " << replayCtrl_->get_play_position(c) << std::endl;
    }
}

uhd::rx_streamer::sptr RfNocFullDuplexGraph::connectForDownload(size_t numRxAntennas) {
    if (numRxAntennas != numRxAntennas_)
        throw UsrpException("Downloading with wrong number of RX antennas!");

    using uhd::rfnoc::block_id_t;
    disconnectAll();

    graph_->release();
    currentRxStreamer_.reset();
    uhd::stream_args_t streamArgs("fc32", "sc16");
    currentRxStreamer_ = graph_->create_rx_streamer(CHANNELS, streamArgs);

    for(size_t i = 0; i < numRxAntennas; i++)
        graph_->connect(block_id_t(blockNames_.replayId), i, currentRxStreamer_, i);
    graph_->commit();

    numRxAntennas_ = numRxAntennas;

    return currentRxStreamer_;

    //_showRfNoCConnections(graph_);
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
}

RfNocFullDuplexGraph::RadioChannelPair RfNocFullDuplexGraph::getRadioChannelPair(int antenna) {
    if (antenna < 2)
        return {radioCtrl1_, antenna};
    else
        return {radioCtrl2_, antenna - 2};
}
}
