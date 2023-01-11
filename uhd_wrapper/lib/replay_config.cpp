#include <chrono>
#include <numeric>

#include "replay_config.hpp"
#include "usrp_exception.hpp"

using namespace std::literals::chrono_literals;

namespace bi {
const int MAX_ANTENNAS = 4;

BlockOffsetTracker::BlockOffsetTracker(size_t sampleSize)
: numStreams_(0), SAMPLE_SIZE(sampleSize) {
    reset();
}

void BlockOffsetTracker::reset() {
    replayIdx_ = -1;
    samplesPerBlock_.clear();
}

void BlockOffsetTracker::setStreamCount(size_t streamCount) {
   numStreams_ = streamCount;
}

void BlockOffsetTracker::checkStreamCount() const {
    if (numStreams_ == 0)
        throw UsrpException("Stream count not set!");
}

void BlockOffsetTracker::recordNewBlock(size_t numSamples) {
    checkStreamCount();
    samplesPerBlock_.push_back(numSamples);
}

void BlockOffsetTracker::replayNextBlock(size_t numSamples) {
    checkStreamCount();
    replayIdx_++;
    if (samplesPerBlock_[replayIdx_] != numSamples)
        throw UsrpException("Incorrect size of replay block");
}

size_t BlockOffsetTracker::samplesUntilBlockNr(size_t blockIdx) const {
    return std::accumulate(samplesPerBlock_.begin(),
                           samplesPerBlock_.begin() + blockIdx,
                           0);
}

size_t BlockOffsetTracker::samplesBeforeCurrentBlock() const {
    assert(samplesPerBlock_.size() > 0);
    return samplesUntilBlockNr(samplesPerBlock_.size() - 1);
}

size_t BlockOffsetTracker::samplesInCurrentBlock() const {
    assert(samplesPerBlock_.size() > 0);
    return samplesPerBlock_[samplesPerBlock_.size() - 1];
}

size_t BlockOffsetTracker::recordOffset(size_t streamIdx) const {
    if (samplesPerBlock_.size() == 0)
        throw UsrpException("No recording started!");
    size_t samplesBefore = samplesBeforeCurrentBlock();
    size_t numSamples = samplesInCurrentBlock();
    return SAMPLE_SIZE * (samplesBefore * numStreams_ + numSamples * streamIdx);
}

size_t BlockOffsetTracker::replayOffset(size_t streamIdx) const {
    if (replayIdx_ < 0)
        throw UsrpException("No replaying started!");
    size_t samplesBefore = samplesUntilBlockNr(replayIdx_);
    size_t numSamples = samplesPerBlock_[replayIdx_];
    return SAMPLE_SIZE * (samplesBefore * numStreams_ + numSamples * streamIdx);
}

ReplayBlockConfig::ReplayBlockConfig(std::shared_ptr<ReplayBlockInterface> replayCtrl)
    : replayBlock_(replayCtrl), MEM_SIZE(replayCtrl->get_mem_size()),
      txBlocks_(SAMPLE_SIZE), rxBlocks_(SAMPLE_SIZE) {
}

void ReplayBlockConfig::setAntennaCount(size_t numTx, size_t numRx) {
    txBlocks_.setStreamCount(numTx);
    rxBlocks_.setStreamCount(numRx);

    numTxAntennas_ = numTx;
    numRxAntennas_ = numRx;
}

void ReplayBlockConfig::reset() {
    txBlocks_.reset();
    rxBlocks_.reset();
}

size_t ReplayBlockConfig::txStreamOffset(size_t numSamples, size_t streamNumber) const {
    return 0;
}

size_t ReplayBlockConfig::rxStreamOffset(size_t numSamples, size_t streamNumber) const {
    return MEM_SIZE / 2 + numSamples * SAMPLE_SIZE * streamNumber;
}

void ReplayBlockConfig::configUpload(size_t numSamples) {
    txBlocks_.recordNewBlock(numSamples);
    const size_t numBytes = numSamples * SAMPLE_SIZE;
    std::lock_guard<std::mutex> lock(replayMtx_);
    for(size_t tx = 0; tx < numTxAntennas_; tx++)
        replayBlock_->record(txBlocks_.recordOffset(tx), numBytes, tx);
    clearRecordingBuffer();
}

void ReplayBlockConfig::configTransmit(size_t numSamples) {
    txBlocks_.replayNextBlock(numSamples);
    std::lock_guard<std::mutex> lock(replayMtx_);
    const size_t numBytes = numSamples * SAMPLE_SIZE;
    for(size_t tx = 0; tx < numTxAntennas_; tx++)
        replayBlock_->config_play(txBlocks_.replayOffset(tx), numBytes, tx);
}

void ReplayBlockConfig::configReceive(size_t numSamples) {
    rxBlocks_.recordNewBlock(numSamples);
    const size_t numBytes = numSamples * SAMPLE_SIZE;
    std::lock_guard<std::mutex> lock(replayMtx_);
    for(size_t rx = 0; rx < numRxAntennas_; rx++)
        replayBlock_->record(MEM_SIZE/2+rxBlocks_.recordOffset(rx), numBytes, rx);
    clearRecordingBuffer();
}

void ReplayBlockConfig::configDownload(size_t numSamples) {
    rxBlocks_.replayNextBlock(numSamples);
    const size_t numBytes = numSamples * SAMPLE_SIZE;
    std::lock_guard<std::mutex> lock(replayMtx_);
    for(size_t rx = 0; rx < numRxAntennas_; rx++)
        replayBlock_->config_play(MEM_SIZE/2+rxBlocks_.replayOffset(rx), numBytes, rx);
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
