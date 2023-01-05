#include "full_duplex_rfnoc_graph.hpp"

namespace bi {

const int CHANNELS=1;

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

uhd::tx_streamer::sptr RfNocFullDuplexGraph::connectForUpload(int numAntennas) {
    disconnectAll();

    graph_->release();
    currentTxStreamer_.reset();
    uhd::stream_args_t streamArgs("fc32", "sc16");
    currentTxStreamer_ = graph_->create_tx_streamer(numAntennas, streamArgs);

    for (int i = 0; i < numAntennas; i++)
        graph_->connect(currentTxStreamer_, i,
                        uhd::rfnoc::block_id_t(blockNames_.replayId), i);


    graph_->commit();
    return currentTxStreamer_;
    // _showRfNoCConnections(graph_);
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
    /*if (currentRxStreamer_) {
        for(int i = 0; i < CHANNELS; i++)
            graph_->disconnect("RxStreamer#0", i);
        currentRxStreamer_.reset();
        }*/

    graph_->commit();
}
}
