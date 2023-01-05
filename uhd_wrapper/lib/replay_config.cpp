#include "replay_config.hpp"
#include "usrp_exception.hpp"

namespace bi {
ReplayBlockConfig::ReplayBlockConfig(std::shared_ptr<ReplayBlockInterface> replayCtrl)
    : replayBlock_(replayCtrl), MEM_SIZE(replayCtrl->get_mem_size()) {
}

void ReplayBlockConfig::setAntennaCount(size_t numTx, size_t numRx) {
    numTxAntennas_ = numTx;
    numRxAntennas_ = numRx;
}

void ReplayBlockConfig::checkAntennaCount() const {
    if (numTxAntennas_ == 0)
        throw UsrpException("TX Antenna count not set!");
    if (numRxAntennas_ == 0)
        throw UsrpException("RX Antenna count not set!");
}

void ReplayBlockConfig::configUpload(size_t numSamples) {
    checkAntennaCount();
    replayBlock_->record(0, numSamples * SAMPLE_SIZE, 0);
}

void ReplayBlockConfig::configTransmit(size_t numSamples) {
    checkAntennaCount();
    replayBlock_->config_play(0, numSamples * SAMPLE_SIZE, 0);
}

void ReplayBlockConfig::configReceive(size_t numSamples) {
    checkAntennaCount();
    replayBlock_->record(MEM_SIZE / 2, numSamples * SAMPLE_SIZE, 0);
}

void ReplayBlockConfig::configDownload(size_t numSamples) {
    checkAntennaCount();
    replayBlock_->config_play(MEM_SIZE / 2, numSamples * SAMPLE_SIZE, 0);
}
}
