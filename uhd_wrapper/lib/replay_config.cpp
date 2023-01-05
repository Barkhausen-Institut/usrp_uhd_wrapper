#include <chrono>

#include "replay_config.hpp"
#include "usrp_exception.hpp"

using namespace std::literals::chrono_literals;

namespace bi {
const int MAX_ANTENNAS = 4;

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
    clearRecordingBuffer();
}

void ReplayBlockConfig::configTransmit(size_t numSamples) {
    checkAntennaCount();
    replayBlock_->config_play(0, numSamples * SAMPLE_SIZE, 0);
}

void ReplayBlockConfig::configReceive(size_t numSamples) {
    checkAntennaCount();
    replayBlock_->record(MEM_SIZE / 2, numSamples * SAMPLE_SIZE, 0);
    clearRecordingBuffer();
}

void ReplayBlockConfig::configDownload(size_t numSamples) {
    checkAntennaCount();
    replayBlock_->config_play(MEM_SIZE / 2, numSamples * SAMPLE_SIZE, 0);
}

void ReplayBlockConfig::clearRecordingBuffer() {
    std::this_thread::sleep_for(10ms);

    bool needClear = false;
    for(int t = 0; t < 3; t++) {
        needClear = false;
        for(int c = 0; c < MAX_ANTENNAS; c++)
            needClear |= (replayBlock_->get_record_fullness(c) > 0);

        if (!needClear)
            break;

        std::cout << "Trying to clear the buffer" << std::endl;
        for(int c = 0; c < MAX_ANTENNAS; c++)
            replayBlock_->record_restart(c);
    }
    if (needClear)
        throw UsrpException("Cannot clear the record buffer!");
}
}
