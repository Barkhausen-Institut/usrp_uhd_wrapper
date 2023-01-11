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

TEST_CASE("BlockOffsetTracker") {
    bi::BlockOffsetTracker tracker(4);

    SECTION("Error checking") {
        tracker.setStreamCount(1);
        SECTION("Throws if recording not started") {
            try {
                tracker.recordOffset(0);
                FAIL("No Exception thrown!");
            }
            catch(bi::UsrpException& e) {
                // done
            }
        }
        SECTION("Throws if replay not started") {
            try {
                tracker.replayOffset(0);
                FAIL("No Exception thrown!");
            }
            catch(bi::UsrpException& e) {
                // done
            }
        }
    }

    SECTION("Single Antenna, single config") {
        tracker.setStreamCount(1);
        tracker.recordNewBlock(15);
        REQUIRE(tracker.recordOffset(0) == 0);

        tracker.replayNextBlock(15);
        REQUIRE(tracker.replayOffset(0) == 0);
    }

    SECTION("Multiple antennas, single config") {
        tracker.setStreamCount(2);
        tracker.recordNewBlock(15);
        REQUIRE(tracker.recordOffset(0) == 0);
        REQUIRE(tracker.recordOffset(1) == 15*4);

        tracker.replayNextBlock(15) ;
        REQUIRE(tracker.replayOffset(0) == 0);
        REQUIRE(tracker.replayOffset(1) == 15*4);
    }

    SECTION("Multiple antenna, multiple configs") {
        tracker.setStreamCount(2);
        tracker.recordNewBlock(15);
        REQUIRE(tracker.recordOffset(0) == 0);
        REQUIRE(tracker.recordOffset(1) == 15*4);
        tracker.recordNewBlock(20);
        REQUIRE(tracker.recordOffset(1) == 15*4*2+20*4);

        tracker.replayNextBlock(15);
        REQUIRE(tracker.replayOffset(0) == 0);
        REQUIRE(tracker.replayOffset(1) == 15*4);
        tracker.replayNextBlock(20);
        REQUIRE(tracker.replayOffset(1) == 15*4*2+20*4);
    }

    SECTION("Can Reset block") {
        tracker.setStreamCount(2);
        tracker.recordNewBlock(15);
        tracker.replayNextBlock(15);
        tracker.reset();

        tracker.recordNewBlock(25);
        REQUIRE(tracker.recordOffset(1) == 25*4);
        tracker.replayNextBlock(25);
        REQUIRE(tracker.replayOffset(1) == 25*4);
    }
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

            REQUIRE_CALL(replay, config_play(0u, 10*4u, 0u));
            block.configTransmit(10);
        }

        SECTION("Reception with 20 samples") {
            REQUIRE_CALL(replay, record(HALF_MEM, 20*4u, 0u));
            block.configReceive(20);

            REQUIRE_CALL(replay, config_play(HALF_MEM, 20*4u, 0u));
            block.configDownload(20);
        }
    }

    SECTION("Two antennas, single config") {
        block.setAntennaCount(2, 2);

        SECTION("Single upload") {
            REQUIRE_CALL(replay, record(0u, 10*4u, 0u));
            REQUIRE_CALL(replay, record(10*4u, 10*4u, 1u));
            block.configUpload(10);

            REQUIRE_CALL(replay, config_play(0u, 10*4u, 0u));
            REQUIRE_CALL(replay, config_play(10*4u, 10*4u, 1u));
            block.configTransmit(10);
        }

        SECTION("Reception with 20 samples") {
            REQUIRE_CALL(replay, record(HALF_MEM, 20*4u, 0u));
            REQUIRE_CALL(replay, record(HALF_MEM+20*4u, 20*4u, 1u));
            block.configReceive(20);

            REQUIRE_CALL(replay, config_play(HALF_MEM, 20*4u, 0u));
            REQUIRE_CALL(replay, config_play(HALF_MEM+20*4u, 20*4u, 1u));
            block.configDownload(20);
        }
    }

    SECTION("Single Antenna, multiple configs") {
        block.setAntennaCount(1, 1);
        trompeloeil::sequence seq;

        REQUIRE_CALL(replay, record(0u, 10*4u, 0u)).IN_SEQUENCE(seq);
        REQUIRE_CALL(replay, record(40u, 15*4u, 0u)).IN_SEQUENCE(seq);
        block.configUpload(10);
        block.configUpload(15);

        REQUIRE_CALL(replay, config_play(0u, 10*4u, 0u)).IN_SEQUENCE(seq);
        REQUIRE_CALL(replay, record(HALF_MEM, 11*4u, 0u)).IN_SEQUENCE(seq);
        block.configTransmit(10);
        block.configReceive(11);

        REQUIRE_CALL(replay, config_play(40u, 15*4u, 0u)).IN_SEQUENCE(seq);
        REQUIRE_CALL(replay, record(HALF_MEM+11*4u, 16*4u, 0u)).IN_SEQUENCE(seq);
        block.configTransmit(15);
        block.configReceive(16);

        REQUIRE_CALL(replay, config_play(HALF_MEM, 11*4u, 0u)).IN_SEQUENCE(seq);
        REQUIRE_CALL(replay, config_play(HALF_MEM+11*4u, 16*4u, 0u)).IN_SEQUENCE(seq);
        block.configDownload(11);
        block.configDownload(16);

    }

}
