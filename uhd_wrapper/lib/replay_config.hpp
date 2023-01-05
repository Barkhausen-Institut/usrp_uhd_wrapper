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


class ReplayBlockConfig {
public:
    ReplayBlockConfig(std::shared_ptr<ReplayBlockInterface> replayCtrl);

    void setAntennaCount(size_t numTx, size_t numRx);
    void configUpload(size_t numSamples);
    void configTransmit(size_t numSamples);
    void configReceive(size_t numSamples);
    void configDownload(size_t numSamples);

private:
    std::shared_ptr<ReplayBlockInterface> replayBlock_;
    const size_t SAMPLE_SIZE = 4;  // 16bit IQ data

    const size_t MEM_SIZE;

    size_t numTxAntennas_ = 0;;
    size_t numRxAntennas_ = 0;;
};
}
