#include "rfnoc_blocks.hpp"
#include <uhd/exception.hpp>

namespace bi {
RfNocBlockConfig RfNocBlockConfig::defaultNames() {
    RfNocBlockConfig result;
    result.radioIds = {"0/Radio#0", "0/Radio#1"};
    result.ducIds = {"0/DUC#0", "0/DUC#1"};
    result.ddcIds = {"0/DDC#0", "0/DDC#1"};

    result.replayId = "0/Replay#0";

    return result;
}

RfNocBlocks::RfNocBlocks(const RfNocBlockConfig& blockNames, uhd::rfnoc::rfnoc_graph::sptr graph)
    : blockNames_(blockNames), graph_(graph) {
    obtainBlocks();
}

void RfNocBlocks::obtainBlocks() {
    using uhd::rfnoc::block_id_t, uhd::rfnoc::radio_control, uhd::rfnoc::replay_block_control;
    using uhd::rfnoc::ddc_block_control, uhd::rfnoc::duc_block_control;

    radioCtrl1_ = graph_->get_block<radio_control>(block_id_t(blockNames_.radioIds[0]));
    radioCtrl2_ = graph_->get_block<radio_control>(block_id_t(blockNames_.radioIds[1]));

    replayCtrl_ = graph_->get_block<replay_block_control>(block_id_t(blockNames_.replayId));

    try {
        ddcControl1_ = graph_->get_block<ddc_block_control>(block_id_t(blockNames_.ddcIds[0]));
        ducControl1_ = graph_->get_block<duc_block_control>(block_id_t(blockNames_.ducIds[0]));
        ddcControl2_ = graph_->get_block<ddc_block_control>(block_id_t(blockNames_.ddcIds[1]));
        ducControl2_ = graph_->get_block<duc_block_control>(block_id_t(blockNames_.ducIds[1]));
    }
    catch(uhd::lookup_error& err) {
        std::cout << "No DDC/DUC found. Disabling decimation" << std::endl;
    }
}

double RfNocBlocks::getCurrentFpgaTime() {
    return graph_->get_mb_controller()->get_timekeeper(0)->get_time_now().get_real_secs();
}

bool RfNocBlocks::supportsDecimation() const {
    return ddcControl1_ != nullptr;
}

size_t RfNocBlocks::getNumAntennas() const {
    return radioCtrl1_->get_num_input_ports() + radioCtrl2_->get_num_input_ports();
}

RfNocBlocks::RadioChannelPair RfNocBlocks::getRadioChannelPair(int antenna) {
    int numAntennasPerRadio = radioCtrl1_->get_num_input_ports();
    if (antenna < numAntennasPerRadio)
        return {radioCtrl1_, antenna};
    else
        return {radioCtrl2_, antenna - numAntennasPerRadio};
}

}
