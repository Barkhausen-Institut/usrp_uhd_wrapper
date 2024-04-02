#include <catch/catch.hpp>
#include <trompeloeil/catch/trompeloeil.hpp>

#include "usrp_exception.hpp"
#include "stream_mapper.hpp"

class StreamMapperDummy : public trompeloeil::mock_interface<bi::StreamMapperBase> {
public:
    IMPLEMENT_MOCK1(configureRxAntenna);
};


TEST_CASE("StreamMapper") {
    StreamMapperDummy mapper;
    (void)mapper;

    bi::RfConfig config;
    config.noTxStreams = 1;
    config.noRxStreams = 1;

    SECTION("Default TX/RX mapping SISO") {
        mapper.setRfConfig(config);
        REQUIRE(mapper.mapTxStreamToAntenna(0) == 0);
        REQUIRE(mapper.mapRxStreamToAntenna(0) == 0);
    }

    SECTION("Default Mapping MIMO") {
        config.noTxStreams = 4;
        config.noRxStreams = 4;
        mapper.setRfConfig(config);
        REQUIRE(mapper.mapTxStreamToAntenna(2) == 2);
        REQUIRE(mapper.mapRxStreamToAntenna(3) == 3);
    }

    SECTION("Can use custom mapping") {
        config.noTxStreams = 4;
        config.txAntennaMapping = {3, 2, 1, 0};
        mapper.setRfConfig(config);

        REQUIRE(mapper.mapTxStreamToAntenna(0) == 3);
        REQUIRE(mapper.mapTxStreamToAntenna(1) == 2);
        REQUIRE(mapper.mapTxStreamToAntenna(3) == 0);
    }

    SECTION("Throws if streamIdx is out of bounds") {
        config.noTxStreams = 1;
        config.noRxStreams = 2;
        mapper.setRfConfig(config);

        REQUIRE_THROWS_AS(mapper.mapTxStreamToAntenna(1), bi::UsrpException);
        REQUIRE_THROWS_AS(mapper.mapRxStreamToAntenna(2), bi::UsrpException);
    }

    SECTION("Throws if mapping and antenna count are not equal") {
        config.noTxStreams = 4;
        config.txAntennaMapping = {1, 2, 3};
        REQUIRE_THROWS_AS(mapper.setRfConfig(config), bi::UsrpException);
    }

    SECTION("Throws if mapping contains invalid antenna numbers") {
        config.noTxStreams = 4;
        config.txAntennaMapping = {0, 1, 2, 4};
        REQUIRE_THROWS_AS(mapper.setRfConfig(config), bi::UsrpException);
    }


}
