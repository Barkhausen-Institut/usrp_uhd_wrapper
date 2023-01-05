#include <catch/catch.hpp>
#include <trompeloeil/catch/trompeloeil.hpp>

#include "replay_config.hpp"

class ReplayMock : public trompeloeil::mock_interface<bi::ReplayBlockInterface> {
public:
    /*MAKE_MOCK3(record, void(const uint64_t, const uint64_t, const size_t));
    MAKE_MOCK0(record_restart, void());
    MAKE_MOCK3(config_play, void(const uint64_t, const uint64_t, const size_t));

    MAKE_MOCK0(get_mem_size, uint64_t() const);
    MAKE_MOCK0(get_record_fullness, uint64_t() const);
    MAKE_MOCK0(get_play_position, uint64_t() const);*/

    IMPLEMENT_MOCK3(record);
    IMPLEMENT_MOCK0(record_restart);
    IMPLEMENT_MOCK3(config_play);

    IMPLEMENT_CONST_MOCK0(get_mem_size);
    IMPLEMENT_CONST_MOCK0(get_record_fullness);
    IMPLEMENT_CONST_MOCK0(get_play_position);
};

TEST_CASE("Sanity") {
    using trompeloeil::_;
    using trompeloeil::gt;
    REQUIRE(1 == 1);

    ReplayMock m;

    REQUIRE_CALL(m, config_play(2u, 5u, 8u));
    m.config_play(2, 5, 8);

}
