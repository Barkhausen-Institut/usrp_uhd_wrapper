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

    void renewSampleRateSettings();

    int getNumTxAntennas() const;
    int getNumRxAntennas() const;
    double getTxSamplingRate() const;
    double getRxSamplingRate() const;
    int getRxDecimationRatio() const;
    double getMasterClockRate() const;

private:
    void setRfConfigForRxAntenna(const RfConfig& conf,
                                 const size_t rxAntennaIdx);
    void setRfConfigForTxAntenna(const RfConfig& conf,
                                 const size_t txAntennaIdx);
    void setRxSampleRate(double rate);
    void setTxSampleRate(double rate);

    RfConfig rfConfig_;
    double masterClockRate_;

    typedef std::tuple<uhd::rfnoc::ddc_block_control::sptr, int> DDCChannelPair;
    DDCChannelPair getDDCChannelPair(int antenna);

    typedef std::tuple<uhd::rfnoc::duc_block_control::sptr, int> DUCChannelPair;
    DUCChannelPair getDUCChannelPair(int antenna);

};
}
