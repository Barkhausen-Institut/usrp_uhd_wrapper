#pragma once

#include <uhd/rfnoc/block_id.hpp>
#include <uhd/rfnoc/radio_control.hpp>
#include <uhd/rfnoc/replay_block_control.hpp>
#include <uhd/rfnoc/duc_block_control.hpp>
#include <uhd/rfnoc/ddc_block_control.hpp>
#include <uhd/rfnoc_graph.hpp>
#include <uhd/rfnoc/mb_controller.hpp>

#include <vector>

using namespace std::literals::chrono_literals;

#include "config.hpp"

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

    uhd::tx_streamer::sptr connectForUpload(size_t numTxAntennas);
    void upload(const MimoSignal& txSignal);

    void connectForStreaming(size_t numTxAntennas, size_t numRxAntennas);
    void stream(double streamTime, size_t numTxSamples, size_t numRxSamples);

    uhd::rx_streamer::sptr connectForDownload(size_t numRxAntennas);
    MimoSignal download(size_t numRxSamples);

private:
    void createRfNocBlocks(const RfNocBlockConfig& config);
    double getCurrentFpgaTime();
    void disconnectAll();

    const size_t PACKET_SIZE = 8192;

    typedef std::tuple<uhd::rfnoc::radio_control::sptr, int> RadioChannelPair;
    RadioChannelPair getRadioChannelPair(int antenna);

    size_t numTxAntennas_, numRxAntennas_;
    uhd::tx_streamer::sptr currentTxStreamer_;
    uhd::rx_streamer::sptr currentRxStreamer_;

    uhd::rfnoc::rfnoc_graph::sptr graph_;
    uhd::rfnoc::radio_control::sptr radioCtrl1_, radioCtrl2_;
    uhd::rfnoc::replay_block_control::sptr replayCtrl_;

    RfNocBlockConfig blockNames_;
};


}
