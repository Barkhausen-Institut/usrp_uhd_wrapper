#pragma once

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
}
