#include "rf_configuration.hpp"

namespace bi {


RFConfiguration::RFConfiguration(const RfNocBlockConfig& blockNames,
                                 uhd::rfnoc::rfnoc_graph::sptr graph)
    : RfNocBlocks(blockNames, graph) {
}
}
