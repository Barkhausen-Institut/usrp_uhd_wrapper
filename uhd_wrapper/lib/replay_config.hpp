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

    virtual size_t get_num_input_ports() const = 0;
    virtual size_t get_num_output_ports() const = 0;
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

    size_t get_num_input_ports() const {
        return replayCtrl_->get_num_input_ports();
    }

    virtual size_t get_num_output_ports() const {
        return replayCtrl_->get_num_output_ports();
    }

private:
    uhd::rfnoc::replay_block_control::sptr replayCtrl_;
};

class BlockOffsetTracker {
public:
    BlockOffsetTracker(size_t memSize, size_t sampleSize);
    void setStreamCount(size_t streamCount);
    void reset();

    void recordNewBlock(size_t numSamples, size_t numRepetitions=1, size_t repetitionPeriod=0);
    size_t recordOffset(size_t streamIdx) const;

    void replayNextBlock(size_t numSamples);
    size_t replayOffset(size_t streamIdx) const;

private:
    struct ReplayBlock {
        size_t numSamples;
        size_t repetitions;
        size_t repetitionPeriod;

        ReplayBlock(size_t numSamples_, size_t repetitions_, size_t repetitionPeriod_)
            : numSamples(numSamples_),
              repetitions(repetitions_),
              repetitionPeriod(repetitionPeriod_)
        {}

        size_t totalSamples() const { return repetitionPeriod * repetitions; }
    };

    size_t byteOffset(size_t sampleOffset) const;

    void checkStreamCount() const;

    size_t numStreams_;
    const size_t MEM_SIZE;
    const size_t SAMPLE_SIZE;
    std::vector<ReplayBlock> replayBlocks_;

    size_t currentRecordBlockStart() const;
    size_t currentRecordBlockLength() const;
    size_t currentRecordBlockEnd() const;
    int currentRepetition_ = -1;
    int currentReplay_ = -1;
};


class ReplayBlockConfig {
public:
    ReplayBlockConfig(std::shared_ptr<ReplayBlockInterface> replayCtrl);

    void setStreamCount(size_t numTx, size_t numRx);
    void reset();
    void configUpload(size_t numSamples);
    void configTransmit(size_t numSamples);
    void configReceive(size_t numSamples);
    void configDownload(size_t numSamples);

private:
    void clearRecordingBuffer();

    std::shared_ptr<ReplayBlockInterface> replayBlock_;
    const size_t SAMPLE_SIZE = 4;  // 16bit IQ data
    const size_t MEM_SIZE;

    size_t numTxStreams_ = 0;;
    size_t numRxStreams_ = 0;;
    std::mutex replayMtx_;

    BlockOffsetTracker txBlocks_, rxBlocks_;
};
}
