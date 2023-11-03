#include "stream_mapper.hpp"

namespace bi {
StreamMapperBase::StreamMapperBase() {
}

StreamMapper::StreamMapper(const RfNocBlockConfig& blockNames,
                           uhd::rfnoc::rfnoc_graph::sptr graph)
    : RfNocBlocks(blockNames, graph) {

    defaultRxPort_ = calculateDefaultRxPort();
    UHD_LOGGER_INFO("uhd_wrapper")  << "Default RX Port: " << defaultRxPort_ << std::endl;
}

void StreamMapper::configureRxAntenna(const RxStreamingConfig &rxConfig) {
    std::string antennaPort = defaultRxPort_;
    if (rxConfig.antennaPort != "")
        antennaPort = rxConfig.antennaPort;
    UHD_LOGGER_INFO("uhd_wrapper") << "Configuring RX Port " << antennaPort;
    for(size_t ant = 0; ant < getNumAntennas(); ant++) {
        auto [radio, channel] = getRadioChannelPair(ant);
        radio->set_rx_antenna(antennaPort, channel);
    }
}

std::string StreamMapper::calculateDefaultRxPort() {
    auto [radio, channel] = getRadioChannelPair(0);
    std::vector<std::string> antennas = radio->get_rx_antennas(channel);

    std::string log = "Avaiable antenna ports: ";
    for(const auto& a: antennas) log += a + " ";
    UHD_LOG_DEBUG("uhd_wrapper", log);

    for(const auto& a: antennas) {
        if (a.rfind("RX", 0) == 0)  // startswith
            return a;
    }
    return antennas[0];
}
}
