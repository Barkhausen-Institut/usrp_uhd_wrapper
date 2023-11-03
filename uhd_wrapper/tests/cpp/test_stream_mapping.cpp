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
}
