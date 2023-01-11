#pragma once
#include <mutex>

#include <uhd/rfnoc/replay_block_control.hpp>

namespace bi {
class ReplayBlockInterface {
public:
    virtual void record(const uint64_t offset, const uint64_t size, const size_t port) = 0;
    virtual void record_restart(const size_t port) = 0;

    virtual uint64_t get_mem_size() const = 0;
    virtual uint64_t get_record_fullness(const size_t port) const = 0;
    virtual uint64_t get_play_position(const size_t port) const = 0;
    virtual void config_play(const uint64_t offset, const uint64_t size, const size_t port) = 0;
};

class ReplayBlockWrapper : public ReplayBlockInterface {
public:
    ReplayBlockWrapper(uhd::rfnoc::replay_block_control::sptr replayCtrl)
        : replayCtrl_(replayCtrl) {}

    void record(const uint64_t offset, const uint64_t size, const size_t port) {
        replayCtrl_->record(offset, size, port);
    }

    void record_restart(const size_t port) {
        replayCtrl_->record_restart(port);
    }

    uint64_t get_mem_size() const { return replayCtrl_->get_mem_size(); };

    uint64_t get_record_fullness(const size_t port) const {
        return replayCtrl_->get_record_fullness(port);
    }

    uint64_t get_play_position(const size_t port) const {
        return replayCtrl_->get_play_position(port);
    }

    void config_play(const uint64_t offset, const uint64_t size, const size_t port) {
        replayCtrl_->config_play(offset, size, port);
    }

private:
    uhd::rfnoc::replay_block_control::sptr replayCtrl_;
};

class BlockOffsetTracker {
public:
    BlockOffsetTracker(size_t sampleSize);
    void setStreamCount(size_t streamCount);
    void reset();

    void recordNewBlock(size_t numSamples);
    size_t recordOffset(size_t streamIdx) const;

    void replayNextBlock(size_t numSamples);
    size_t replayOffset(size_t streamIdx) const;

private:
    void checkStreamCount() const;
    size_t samplesUntilBlockNr(size_t blockIdx) const;
    size_t samplesInCurrentBlock() const;
    size_t samplesBeforeCurrentBlock() const;

    size_t numStreams_;
    const size_t SAMPLE_SIZE;
    std::vector<size_t> samplesPerBlock_;
    int replayIdx_ = -1;

};


class ReplayBlockConfig {
public:
    ReplayBlockConfig(std::shared_ptr<ReplayBlockInterface> replayCtrl);

    void setAntennaCount(size_t numTx, size_t numRx);
    void configUpload(size_t numSamples);
    void configTransmit(size_t numSamples);
    void configReceive(size_t numSamples);
    void configDownload(size_t numSamples);

private:
    void clearRecordingBuffer();

    size_t txStreamOffset(size_t numSamples, size_t streamNumber) const;
    size_t rxStreamOffset(size_t numSamples, size_t streamNumber) const;

    std::shared_ptr<ReplayBlockInterface> replayBlock_;
    const size_t SAMPLE_SIZE = 4;  // 16bit IQ data

    const size_t MEM_SIZE;

    size_t numTxAntennas_ = 0;;
    size_t numRxAntennas_ = 0;;

    std::mutex replayMtx_;

    BlockOffsetTracker txBlocks_, rxBlocks_;
};
}
