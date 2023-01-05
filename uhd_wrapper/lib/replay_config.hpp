#pragma once

#include <uhd/rfnoc/replay_block_control.hpp>

namespace bi {
class ReplayBlockInterface {
public:
    virtual void record(const uint64_t offset, const uint64_t size, const size_t port) = 0;
    virtual void record_restart() = 0;

    virtual uint64_t get_mem_size() const = 0;
    virtual uint64_t get_record_fullness() const = 0;
    virtual uint64_t get_play_position() const = 0;
    virtual void config_play(const uint64_t offset, const uint64_t size, const size_t port) = 0;
};

class ReplayBlockWrapper : public ReplayBlockInterface {
public:
    ReplayBlockWrapper(uhd::rfnoc::replay_block_control::sptr replayCtrl)
        : replayCtrl_(replayCtrl) {}

    void record(const uint64_t offset, const uint64_t size, const size_t port) {
        replayCtrl_->record(offset, size, port);
    }
    void record_restart() { replayCtrl_->record_restart(); }

    uint64_t get_mem_size() const { return replayCtrl_->get_mem_size(); };
    uint64_t get_record_fullness() const { return replayCtrl_->get_record_fullness(); }
    uint64_t get_play_position() const { return replayCtrl_->get_play_position(); }

    void config_play(const uint64_t offset, const uint64_t size, const size_t port) {
        replayCtrl_->config_play(offset, size, port);
    }

private:
    uhd::rfnoc::replay_block_control::sptr replayCtrl_;
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
    void checkAntennaCount() const;

    std::shared_ptr<ReplayBlockInterface> replayBlock_;
    const size_t SAMPLE_SIZE = 4;  // 16bit IQ data

    const size_t MEM_SIZE;

    size_t numTxAntennas_ = 0;;
    size_t numRxAntennas_ = 0;;
};
}
