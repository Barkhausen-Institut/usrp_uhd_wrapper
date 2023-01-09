#include <catch/catch.hpp>
#include <trompeloeil/catch/trompeloeil.hpp>

#include "usrp_exception.hpp"

#include "replay_config.hpp"

class ReplayMock : public trompeloeil::mock_interface<bi::ReplayBlockInterface> {
public:
    IMPLEMENT_MOCK3(record);
    IMPLEMENT_MOCK1(record_restart);
    IMPLEMENT_MOCK3(config_play);

    IMPLEMENT_CONST_MOCK0(get_mem_size);
    IMPLEMENT_CONST_MOCK1(get_record_fullness);
    IMPLEMENT_CONST_MOCK1(get_play_position);
};

TEST_CASE("Sanity") {
    REQUIRE(1 == 1);

    ReplayMock m;

    REQUIRE_CALL(m, config_play(2u, 5u, 8u));
    m.config_play(2, 5, 8);
}

TEST_CASE("Replay Block Config") {
    using trompeloeil::_;

    ReplayMock replay;
    uint64_t MEM_SIZE = 8192;
    uint64_t HALF_MEM = MEM_SIZE / 2;

    ALLOW_CALL(replay, get_mem_size()).RETURN(MEM_SIZE);
    ALLOW_CALL(replay, get_record_fullness(_)).RETURN(0);


    std::shared_ptr<bi::ReplayBlockInterface> ptrReplay(&replay, [](auto) {});
    bi::ReplayBlockConfig block(ptrReplay);

    SECTION("Throws if antenna count is not set or too small") {
        // cannot use require_throws_as due to https://github.com/catchorg/Catch2/issues/1292
        try {
            block.configUpload(5);
            FAIL("No exception thrown!");
        }
        catch(bi::UsrpException& ) {
        }
    }

    SECTION("Single Antenna") {
        block.setAntennaCount(1, 1);

        SECTION("Single upload with 10 samples") {
            REQUIRE_CALL(replay, record(0u, 10*4u, 0u));
            block.configUpload(10);
        }

        SECTION("Transmission with 15 samples") {
            REQUIRE_CALL(replay, config_play(0u, 15*4u, 0u));
            block.configTransmit(15);
        }

        SECTION("Reception with 20 samples") {
            REQUIRE_CALL(replay, record(HALF_MEM, 20*4u, 0u));
            block.configReceive(20);
        }

        SECTION("Download with 25 samples") {
            REQUIRE_CALL(replay, config_play(HALF_MEM, 25*4u, 0u));
            block.configDownload(25);
        }
    }

    SECTION("Two antennas, single config") {
        block.setAntennaCount(2, 2);

        SECTION("Single upload") {
            REQUIRE_CALL(replay, record(0u, 10*4u, 0u));
            REQUIRE_CALL(replay, record(10*4u, 10*4u, 1u));
            block.configUpload(10);
        }

        SECTION("Transmission with 15 samples") {
            REQUIRE_CALL(replay, config_play(0u, 15*4u, 0u));
            REQUIRE_CALL(replay, config_play(15*4u, 15*4u, 1u));
            block.configTransmit(15);
        }

        SECTION("Reception with 20 samples") {
            REQUIRE_CALL(replay, record(HALF_MEM, 20*4u, 0u));
            REQUIRE_CALL(replay, record(HALF_MEM+20*4u, 20*4u, 1u));
            block.configReceive(20);
        }

        SECTION("Download with 25 samples") {
            REQUIRE_CALL(replay, config_play(HALF_MEM, 25*4u, 0u));
            REQUIRE_CALL(replay, config_play(HALF_MEM+25*4u, 25*4u, 1u));
            block.configDownload(25);
        }
    }


}
