#pragma once

#include <uhd/rfnoc/block_id.hpp>
#include <uhd/rfnoc/radio_control.hpp>
#include <uhd/rfnoc/replay_block_control.hpp>
#include <uhd/rfnoc/duc_block_control.hpp>
#include <uhd/rfnoc/ddc_block_control.hpp>
#include <uhd/rfnoc_graph.hpp>

#include <vector>

namespace bi {

struct RfNocBlockConfig {
    std::vector<std::string> radioIds;
    std::vector<std::string> ducIds;
    std::vector<std::string> ddcIds;
    std::string replayId;
};

class RfNocFullDuplexGraph {
public:
    RfNocFullDuplexGraph(uhd::rfnoc::rfnoc_graph::sptr graph, const RfNocBlockConfig& config);

    uhd::tx_streamer::sptr connectForUpload(int numAntennas);
    void connectForStreaming(int numAntennas);
    uhd::rx_streamer::sptr connectForDownload(int numAntennas);

private:
    void createRfNocBlocks(const RfNocBlockConfig& config);
    void disconnectAll();

    uhd::tx_streamer::sptr currentTxStreamer_;

    uhd::rfnoc::rfnoc_graph::sptr graph_;
    uhd::rfnoc::radio_control::sptr radioCtrl1_, radioCtrl2_;
    uhd::rfnoc::replay_block_control::sptr replayCtrl_;

    RfNocBlockConfig blockNames_;
};


}
