#include "stream_mapper.hpp"
#include "usrp_exception.hpp"

const int NUM_ANTENNAS = 4;

namespace bi {
StreamMapperBase::StreamMapperBase() {
}

void StreamMapperBase::setRfConfig(const RfConfig &config) {
    if (config.txAntennaMapping.size() > 0) {
        checkMapping(config.txAntennaMapping, config.noTxAntennas);
        txMapping_ = config.txAntennaMapping;
    }
    else
        txMapping_ = defaultMapping(config.noTxAntennas);

    if (config.rxAntennaMapping.size() > 0) {
        checkMapping(config.rxAntennaMapping, config.noRxAntennas);
        rxMapping_ = config.rxAntennaMapping;
    }
    else
        rxMapping_ = defaultMapping(config.noRxAntennas);
}

void StreamMapperBase::applyDefaultMapping(int numStreams) {
    txMapping_ = defaultMapping(numStreams);
    rxMapping_ = defaultMapping(numStreams);
}

void StreamMapperBase::checkMapping(const StreamMapperBase::Mapping& mapping,
                                    uint numStreams) {
    if (mapping.size() != numStreams)
        throw UsrpException("Mapping length does not equal antenna count");

    for (uint t = 0; t < mapping.size(); t++) {
        if (mapping[t] >= NUM_ANTENNAS)
            throw UsrpException("Mapping contains an invalid antenna idx!");
    }
}

StreamMapperBase::Mapping StreamMapperBase::defaultMapping(uint numStreams) const {
    Mapping result;
    for (uint s = 0; s < numStreams; s++)
        result.push_back(s);
    return result;
}

uint StreamMapperBase::mapTxStreamToAntenna(uint streamIdx) const {
    return mapStreamToAntenna(streamIdx, txMapping_);
}

uint StreamMapperBase::mapRxStreamToAntenna(uint streamIdx) const {
    return mapStreamToAntenna(streamIdx, rxMapping_);
}

uint StreamMapperBase::mapStreamToAntenna(uint streamIdx,
                                          const StreamMapperBase::Mapping& mapping) const {
    if (streamIdx >= mapping.size())
        throw UsrpException("Stream Idx out of bounds");
    return mapping[streamIdx];
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
