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

    IMPLEMENT_CONST_MOCK0(get_num_input_ports);
    IMPLEMENT_CONST_MOCK0(get_num_output_ports);
};

TEST_CASE("Sanity") {
    REQUIRE(1 == 1);

    ReplayMock m;

    REQUIRE_CALL(m, config_play(2u, 5u, 8u));
    m.config_play(2, 5, 8);
}

TEST_CASE("BlockOffsetTracker") {
    size_t MEM_SIZE = 1000;
    bi::BlockOffsetTracker tracker(MEM_SIZE, 4);

    SECTION("Error checking") {
        tracker.setStreamCount(1);
        SECTION("Throws if recording not started") {
            REQUIRE_THROWS_AS(tracker.recordOffset(0), bi::UsrpException);
        }
        SECTION("Throws if replay not started") {
            REQUIRE_THROWS_AS(tracker.replayOffset(0), bi::UsrpException);
        }

        SECTION("Throws if more replay than records") {
            tracker.recordNewBlock(5);
            tracker.replayNextBlock(5);
            REQUIRE_THROWS_AS(tracker.replayNextBlock(5), bi::UsrpException);
        }

        SECTION("Throws if too much memory would be used") {
            tracker.recordNewBlock(5);
            REQUIRE_THROWS_AS(tracker.recordNewBlock(MEM_SIZE/4), bi::UsrpException);
            REQUIRE_THROWS_AS(tracker.recordNewBlock(10, 5, 100), bi::UsrpException);
        }

        SECTION("RepetitionPeriod must be larger than numSamples") {
            REQUIRE_THROWS_AS(tracker.recordNewBlock(10, 1, 9), bi::UsrpException);
        }

    }

    SECTION("Single stream, single config") {
        tracker.setStreamCount(1);
        tracker.recordNewBlock(15);
        REQUIRE(tracker.recordOffset(0) == 0);

        tracker.replayNextBlock(15);
        REQUIRE(tracker.replayOffset(0) == 0);
    }

    SECTION("Multiple streams, single config") {
        tracker.setStreamCount(2);
        tracker.recordNewBlock(15);
        REQUIRE(tracker.recordOffset(0) == 0);
        REQUIRE(tracker.recordOffset(1) == 15*4);

        tracker.replayNextBlock(15) ;
        REQUIRE(tracker.replayOffset(0) == 0);
        REQUIRE(tracker.replayOffset(1) == 15*4);
    }

    SECTION("Multiple streams, multiple configs") {
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

    SECTION("Single stream, single config with repetitions") {
        tracker.setStreamCount(1);
        const size_t REP = 5;
        const size_t PERIOD = 30;
        const size_t SAMPLES = 10;
        tracker.recordNewBlock(SAMPLES, REP, PERIOD);
        REQUIRE(tracker.recordOffset(0) == 0);
        for (size_t i = 0; i < REP; i++) {
            tracker.replayNextBlock(SAMPLES);
            REQUIRE(tracker.replayOffset(0) == PERIOD * i * 4);
        }
    }

    SECTION("Single stream, multiple configs with repetitions") {
        tracker.setStreamCount(1);
        tracker.recordNewBlock(10, 5, 30);
        REQUIRE(tracker.recordOffset(0) == 0);
        tracker.recordNewBlock(45);
        REQUIRE(tracker.recordOffset(0) == 30*5*4);

        for(int i = 0; i < 5; i++) tracker.replayNextBlock(10);
        tracker.replayNextBlock(45);
        REQUIRE(tracker.replayOffset(0) == 5*30*4);
    }

    SECTION("Multiple Streams, single config with repetition") {
        // multiple streams with repetitions is not implemented
        tracker.setStreamCount(2);
        REQUIRE_THROWS_AS(tracker.recordNewBlock(5, 2, 10), bi::UsrpException);
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
    uint64_t RX_OFFSET = MEM_SIZE / 4;

    ALLOW_CALL(replay, get_mem_size()).RETURN(MEM_SIZE);
    ALLOW_CALL(replay, get_record_fullness(_)).RETURN(0);
    ALLOW_CALL(replay, get_num_input_ports()).RETURN(4);
    ALLOW_CALL(replay, get_num_output_ports()).RETURN(4);


    std::shared_ptr<bi::ReplayBlockInterface> ptrReplay(&replay, [](auto) {});
    bi::ReplayBlockConfig block(ptrReplay);

    SECTION("Correct Buffer Sizes") {
        REQUIRE(block.getTxBufferSize() == RX_OFFSET);
        REQUIRE(block.getRxBufferSize() == MEM_SIZE - RX_OFFSET);
        REQUIRE(block.getRxBufferOffset() == RX_OFFSET);
    }

    SECTION("Throws if streams count is not set or too small") {
        // cannot use require_throws_as due to https://github.com/catchorg/Catch2/issues/1292
        try {
            block.configUpload(5);
            FAIL("No exception thrown!");
        }
        catch(bi::UsrpException& ) {
        }
    }

    SECTION("Single stream") {
        block.setStreamCount(1, 1);

        SECTION("Single upload with 10 samples") {
            REQUIRE_CALL(replay, record(0u, 10*4u, 0u));
            block.configUpload(10);

            REQUIRE_CALL(replay, config_play(0u, 10*4u, 0u));
            block.configTransmit(10);
        }

        SECTION("Reception with 20 samples") {
            REQUIRE_CALL(replay, record(RX_OFFSET, 20*4u, 0u));
            block.configReceive(20);

            REQUIRE_CALL(replay, config_play(RX_OFFSET, 20*4u, 0u));
            block.configDownload(20);
        }
    }

    SECTION("Two streams, single config") {
        block.setStreamCount(2, 2);

        SECTION("Single upload") {
            REQUIRE_CALL(replay, record(0u, 10*4u, 0u));
            REQUIRE_CALL(replay, record(10*4u, 10*4u, 1u));
            block.configUpload(10);

            REQUIRE_CALL(replay, config_play(0u, 10*4u, 0u));
            REQUIRE_CALL(replay, config_play(10*4u, 10*4u, 1u));
            block.configTransmit(10);
        }

        SECTION("Reception with 20 samples") {
            REQUIRE_CALL(replay, record(RX_OFFSET, 20*4u, 0u));
            REQUIRE_CALL(replay, record(RX_OFFSET+20*4u, 20*4u, 1u));
            block.configReceive(20);

            REQUIRE_CALL(replay, config_play(RX_OFFSET, 20*4u, 0u));
            REQUIRE_CALL(replay, config_play(RX_OFFSET+20*4u, 20*4u, 1u));
            block.configDownload(20);
        }
    }

    SECTION("Single stream, multiple configs") {
        block.setStreamCount(1, 1);
        trompeloeil::sequence seq;

        REQUIRE_CALL(replay, record(0u, 10*4u, 0u)).IN_SEQUENCE(seq);
        REQUIRE_CALL(replay, record(40u, 15*4u, 0u)).IN_SEQUENCE(seq);
        block.configUpload(10);
        block.configUpload(15);

        REQUIRE_CALL(replay, config_play(0u, 10*4u, 0u)).IN_SEQUENCE(seq);
        REQUIRE_CALL(replay, record(RX_OFFSET, 11*4u, 0u)).IN_SEQUENCE(seq);
        block.configTransmit(10);
        block.configReceive(11);

        REQUIRE_CALL(replay, config_play(40u, 15*4u, 0u)).IN_SEQUENCE(seq);
        REQUIRE_CALL(replay, record(RX_OFFSET+11*4u, 16*4u, 0u)).IN_SEQUENCE(seq);
        block.configTransmit(15);
        block.configReceive(16);

        REQUIRE_CALL(replay, config_play(RX_OFFSET, 11*4u, 0u)).IN_SEQUENCE(seq);
        REQUIRE_CALL(replay, config_play(RX_OFFSET+11*4u, 16*4u, 0u)).IN_SEQUENCE(seq);
        block.configDownload(11);
        block.configDownload(16);
    }

    SECTION("Single stream, repetitions") {
        block.setStreamCount(1, 1);
        trompeloeil::sequence seq;

        REQUIRE_CALL(replay, record(RX_OFFSET, 2*50*4u, 0u));
        block.configReceive(20, 2, 50);

        REQUIRE_CALL(replay, config_play(RX_OFFSET+0*50*4u, 20 * 4u, 0u));
        REQUIRE_CALL(replay, config_play(RX_OFFSET+1*50*4u, 20 * 4u, 0u));
        block.configDownload(20);
        block.configDownload(20);
    }
}
