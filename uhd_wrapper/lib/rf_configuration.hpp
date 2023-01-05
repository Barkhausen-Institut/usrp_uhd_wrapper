#pragma once

#include <uhd/rfnoc/block_id.hpp>
#include <uhd/rfnoc/radio_control.hpp>
#include <uhd/rfnoc/replay_block_control.hpp>
#include <uhd/rfnoc/duc_block_control.hpp>
#include <uhd/rfnoc/ddc_block_control.hpp>
#include <uhd/rfnoc_graph.hpp>
#include <uhd/rfnoc/mb_controller.hpp>

#include "config.hpp"
#include "rfnoc_blocks.hpp"

namespace bi {


class RFConfiguration : private RfNocBlocks {
public:
    RFConfiguration(const RfNocBlockConfig& blockNames,
                    uhd::rfnoc::rfnoc_graph::sptr graph);

    RfConfig readFromGraph();
    void setRfConfig(const RfConfig& config);

    void renewSamplerateSettings();

private:
    RfConfig rfConfig_;

};
}
