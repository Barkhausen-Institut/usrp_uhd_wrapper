#include "stream_mapper.hpp"

namespace bi {
StreamMapperBase::StreamMapperBase() {
}

StreamMapper::StreamMapper(const RfNocBlockConfig& blockNames,
                           uhd::rfnoc::rfnoc_graph::sptr graph)
    : RfNocBlocks(blockNames, graph) {
}

void StreamMapper::configureRxAntenna(const RxStreamingConfig &rxConfig) {
    for(size_t ant = 0; ant < getNumAntennas(); ant++) {
        auto [radio, channel] = getRadioChannelPair(ant);
        std::string antennaPort = "RX2";
        if (rxConfig.antennaPort != "")
            antennaPort = rxConfig.antennaPort;
        radio->set_rx_antenna(antennaPort, channel);
    }
}
}
