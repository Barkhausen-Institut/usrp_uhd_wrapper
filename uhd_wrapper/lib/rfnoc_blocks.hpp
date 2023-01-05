
#pragma once

#include <uhd/rfnoc/block_id.hpp>
#include <uhd/rfnoc/radio_control.hpp>
#include <uhd/rfnoc/replay_block_control.hpp>
#include <uhd/rfnoc/duc_block_control.hpp>
#include <uhd/rfnoc/ddc_block_control.hpp>
#include <uhd/rfnoc_graph.hpp>
#include <uhd/rfnoc/mb_controller.hpp>

#include "config.hpp"

namespace bi {

struct RfNocBlockConfig {
    std::vector<std::string> radioIds;
    std::vector<std::string> ducIds;
    std::vector<std::string> ddcIds;
    std::string replayId;
};

class RfNocBlocks {
public:
    RfNocBlocks(const RfNocBlockConfig& blockNames, uhd::rfnoc::rfnoc_graph::sptr graph);

    RfNocBlockConfig blockNames_;

    uhd::rfnoc::rfnoc_graph::sptr graph_;

    uhd::rfnoc::radio_control::sptr radioCtrl1_, radioCtrl2_;
    uhd::rfnoc::replay_block_control::sptr replayCtrl_;
    uhd::rfnoc::duc_block_control::sptr ducControl1_, ducControl2_;
    uhd::rfnoc::ddc_block_control::sptr ddcControl1_, ddcControl2_;

private:
    void obtainBlocks();
};


}
