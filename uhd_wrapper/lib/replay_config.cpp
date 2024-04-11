#include <chrono>
#include <numeric>

#include "replay_config.hpp"
#include "usrp_exception.hpp"

using namespace std::literals::chrono_literals;

namespace bi {

BlockOffsetTracker::BlockOffsetTracker(size_t memSize, size_t sampleSize)
: numStreams_(0), MEM_SIZE(memSize), SAMPLE_SIZE(sampleSize) {
    reset();
}

void BlockOffsetTracker::reset() {
    replayBlocks_.clear();
    currentRepetition_ = -1;
    currentReplay_ = -1;
}

void BlockOffsetTracker::setStreamCount(size_t streamCount) {
   numStreams_ = streamCount;
}

void BlockOffsetTracker::checkStreamCount() const {
    if (numStreams_ == 0)
        throw UsrpException("Stream count not set!");
}

void BlockOffsetTracker::recordNewBlock(size_t numSamples,
                                        size_t numRepetitions,
                                        size_t repetitionPeriod) {
    checkStreamCount();
    if (repetitionPeriod == 0)
        repetitionPeriod = numSamples;
    if (repetitionPeriod < numSamples)
        throw UsrpException("RepetitionPeriod must be >= numSamples");
    if (numRepetitions > 1 && numStreams_ > 1)
        throw UsrpException("Multi-Stream with Repetitions not implemented!");

    ReplayBlock block(numSamples, numRepetitions, repetitionPeriod);
    if (byteOffset(currentRecordBlockEnd() + block.totalSamples() * numStreams_) >= MEM_SIZE)
        throw UsrpException("Attempting to store too many samples in buffer!");

    replayBlocks_.push_back(block);
}

void BlockOffsetTracker::replayNextBlock(size_t numSamples) {
    checkStreamCount();

    currentRepetition_++;
    int repsInCurrentBlock = 0;
    if (currentReplay_ >= 0)
        repsInCurrentBlock = replayBlocks_[currentReplay_].repetitions;
    if (currentRepetition_ >= repsInCurrentBlock) {
        currentReplay_++;
        currentRepetition_ = 0;
    }
    if (currentReplay_ >= (int)replayBlocks_.size())
        throw UsrpException("Too many replay requests!");
}

size_t BlockOffsetTracker::byteOffset(size_t samplesOffset) const {
    return samplesOffset * SAMPLE_SIZE;
}

size_t BlockOffsetTracker::recordOffset(size_t streamIdx) const {
    if (replayBlocks_.size() == 0)
        throw UsrpException("Recording not started!");
    return byteOffset(currentRecordBlockStart() + currentRecordBlockLength() * streamIdx);
}

size_t BlockOffsetTracker::currentRecordBlockStart() const {
    if (replayBlocks_.size() == 0)
        return 0;

    size_t off = 0;
    for(size_t i = 0; i < replayBlocks_.size() - 1; i++)
        off += replayBlocks_[i].totalSamples() * numStreams_;
    return off;
}

size_t BlockOffsetTracker::currentRecordBlockEnd() const {
    return currentRecordBlockStart() + numStreams_ * currentRecordBlockLength();
}

size_t BlockOffsetTracker::currentRecordBlockLength() const {
    if (replayBlocks_.size() == 0)
        return 0;
    return replayBlocks_.back().totalSamples();
}

size_t BlockOffsetTracker::replayOffset(size_t streamIdx) const {
    if (currentRepetition_ == -1)
        throw UsrpException("Replaying not started!");

    size_t offsetBefore = 0;
    for (int i = 0; i < currentReplay_; i++)
        offsetBefore += replayBlocks_[i].totalSamples() * numStreams_;
    const ReplayBlock& currentBlock = replayBlocks_[currentReplay_];
    offsetBefore += currentRepetition_ * currentBlock.repetitionPeriod;

    return byteOffset(offsetBefore + currentBlock.totalSamples() * streamIdx);
}

ReplayBlockConfig::ReplayBlockConfig(std::shared_ptr<ReplayBlockInterface> replayCtrl)
    : replayBlock_(replayCtrl), MEM_SIZE(replayCtrl->get_mem_size()),
      txBlocks_(MEM_SIZE/2, SAMPLE_SIZE), rxBlocks_(MEM_SIZE/2, SAMPLE_SIZE) {
}

void ReplayBlockConfig::setStreamCount(size_t numTx, size_t numRx) {
    txBlocks_.setStreamCount(numTx);
    rxBlocks_.setStreamCount(numRx);

    numTxStreams_ = numTx;
    numRxStreams_ = numRx;
}

void ReplayBlockConfig::reset() {
    txBlocks_.reset();
    rxBlocks_.reset();
}

void ReplayBlockConfig::configUpload(size_t numSamples) {
    txBlocks_.recordNewBlock(numSamples);
    const size_t numBytes = numSamples * SAMPLE_SIZE;
    std::lock_guard<std::mutex> lock(replayMtx_);
    for(size_t tx = 0; tx < numTxStreams_; tx++)
        replayBlock_->record(txBlocks_.recordOffset(tx), numBytes, tx);
    clearRecordingBuffer();
}

void ReplayBlockConfig::configTransmit(size_t numSamples) {
    txBlocks_.replayNextBlock(numSamples);
    std::lock_guard<std::mutex> lock(replayMtx_);
    const size_t numBytes = numSamples * SAMPLE_SIZE;
    for(size_t tx = 0; tx < numTxStreams_; tx++)
        replayBlock_->config_play(txBlocks_.replayOffset(tx), numBytes, tx);
}

void ReplayBlockConfig::configReceive(size_t numSamples) {
    rxBlocks_.recordNewBlock(numSamples);
    const size_t numBytes = numSamples * SAMPLE_SIZE;
    std::lock_guard<std::mutex> lock(replayMtx_);
    for(size_t rx = 0; rx < numRxStreams_; rx++)
        replayBlock_->record(MEM_SIZE/2+rxBlocks_.recordOffset(rx), numBytes, rx);
    clearRecordingBuffer();
}

void ReplayBlockConfig::configDownload(size_t numSamples) {
    rxBlocks_.replayNextBlock(numSamples);
    const size_t numBytes = numSamples * SAMPLE_SIZE;
    std::lock_guard<std::mutex> lock(replayMtx_);
    for(size_t rx = 0; rx < numRxStreams_; rx++)
        replayBlock_->config_play(MEM_SIZE/2+rxBlocks_.replayOffset(rx), numBytes, rx);
}

void ReplayBlockConfig::clearRecordingBuffer() {
    std::this_thread::sleep_for(10ms);

    int numPorts = replayBlock_->get_num_input_ports();

    bool needClear = false;
    for(int t = 0; t < 3; t++) {
        needClear = false;
        for(int c = 0; c < numPorts; c++)
            needClear |= (replayBlock_->get_record_fullness(c) > 0);

        if (!needClear)
            break;

        std::cout << "Trying to clear the buffer" << std::endl;
        for(int c = 0; c < numPorts; c++)
            replayBlock_->record_restart(c);
    }
    if (needClear)
        throw UsrpException("Cannot clear the record buffer!");
}
}
