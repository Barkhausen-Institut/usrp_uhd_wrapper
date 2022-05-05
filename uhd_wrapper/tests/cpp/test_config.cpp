/** @file
 *
 * This file serves to
 * 1. demonstrate how the catch file is to be included (without #define !) and
 * 2. to provide a test skeleton using catch2.
 **/

#include "catch/catch.hpp"
#include "config.hpp"
#include "usrp_exception.hpp"

namespace bi {
TEST_CASE("[SamplesDoNotFitEvenlyIntoBuffer]") {
    SECTION("No samples in last package") {
        REQUIRE(calcNoPackages(4000, 2000) == 2);
        REQUIRE(calcNoSamplesLastBuffer(4000, 2000) == 2000);
    }
    SECTION("Ten samples in last package") {
        REQUIRE(calcNoPackages(4010, 2000) == 3);
        REQUIRE(calcNoSamplesLastBuffer(4010, 2000) == 10);
    }
    SECTION("one package not entirely filled") {
        REQUIRE(calcNoPackages(999, 2000) == 1);
        REQUIRE(calcNoSamplesLastBuffer(999, 2000) == 999);
    }
}

TEST_CASE("[SamplingRateSupported]") {
    SECTION("Uneven decimation rate throws exception") {
        REQUIRE_THROWS_AS(assertSamplingRate(250e6 / 3, 250e6), UsrpException);
    }

    SECTION("Even decimation rate throws no exception") {
        REQUIRE_NOTHROW(assertSamplingRate(250e6 / 4, 250e6));
    }
    SECTION("Full sample rate throws no exception") {
        REQUIRE_NOTHROW(assertSamplingRate(250e6 / 1, 250e6));
    }
}

TEST_CASE("[ValidTxStreamingConfig]") {
    double guardOffset = 1.0;
    double fs = 20000.0;
    TxStreamingConfig prevConfig;
    prevConfig.samples = {{bi::samples_vec(2000, bi::sample(1.0, 1.0))}};
    prevConfig.sendTimeOffset = 0.0;

    TxStreamingConfig newConfig;
    newConfig.samples = {{}};
    newConfig.sendTimeOffset = prevConfig.sendTimeOffset + guardOffset +
                               prevConfig.samples[0].size() / fs;
    SECTION("NewOffsetIsValid") {
        REQUIRE_NOTHROW(assertValidTxStreamingConfig(prevConfig, newConfig,
                                                     guardOffset, fs));
    }
    SECTION("NewOffsetSmallerThanPrevious") {
        prevConfig.sendTimeOffset = 1.0;
        newConfig.sendTimeOffset = 0.0;
        REQUIRE_THROWS_AS(assertValidTxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }

    SECTION("NewOffsetSmallerThanGuardOffset") {
        double guardOffset = 1.0;
        prevConfig.samples = {{}};
        prevConfig.sendTimeOffset = 1.0;
        prevConfig.sendTimeOffset = 1.0 + guardOffset / 2;
        REQUIRE_THROWS_AS(assertValidTxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }

    SECTION("NewOffsetSmallerThanDurationOfPreviousSignal") {
        prevConfig.sendTimeOffset = 1.0;
        prevConfig.sendTimeOffset = 1.0 + guardOffset;
        REQUIRE_THROWS_AS(assertValidTxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }
}
}  // namespace bi