#pragma once
#include <mutex>

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
#include "rfnoc_blocks.hpp"
#include "stream_mapper.hpp"

namespace bi {


class RfNocFullDuplexGraph : private RfNocBlocks {
public:
    RfNocFullDuplexGraph(const RfNocBlockConfig& config,
                         uhd::rfnoc::rfnoc_graph::sptr graph,
                         const StreamMapper& streamMapper);
    uhd::rfnoc::replay_block_control::sptr getReplayControl();

    using RfNocBlocks::getNumAntennas;

    void setSyncSource(const std::string& type);

    uhd::tx_streamer::sptr connectForUpload(size_t numTxStreams);
    void upload(const MimoSignal& txSignal);

    void connectForStreaming(size_t numTxStreams, size_t numRxStreams);
    void transmit(double streamTime, size_t numTxSamples, double signalDuration);
    void receive(double streamTime, size_t numRxSamples, double signalDuration);

    uhd::rx_streamer::sptr connectForDownload(size_t numRxStreams);
    MimoSignal download(size_t numRxSamples);

private:
    void disconnectAll();

    const size_t PACKET_SIZE = 8192 / 2;

    const StreamMapper& streamMapper_;
    std::string currentSyncSource_;
    size_t numTxStreams_, numRxStreams_;
    uhd::tx_streamer::sptr currentTxStreamer_;
    uhd::rx_streamer::sptr currentRxStreamer_;
    mutable std::recursive_mutex fpgaAccessMutex_;
};


}
