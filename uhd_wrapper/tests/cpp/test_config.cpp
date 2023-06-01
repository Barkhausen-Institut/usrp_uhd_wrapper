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
        REQUIRE_THROWS_AS(assertSamplingRate(250e6 / 3, 250e6, true), UsrpException);
    }

    SECTION("Even decimation rate throws no exception") {
        REQUIRE_NOTHROW(assertSamplingRate(250e6 / 4, 250e6, true));
    }
    SECTION("Full sample rate throws no exception") {
        REQUIRE_NOTHROW(assertSamplingRate(250e6 / 1, 250e6, true));
    }

    SECTION("Close-to-correct-samplerate throws no error") {
        REQUIRE_NOTHROW(assertSamplingRate(4.38857143e+06, 245.76e6, true));
    }

    SECTION("Allow only master clock rate when no decimation allowed") {
        REQUIRE_THROWS_AS(assertSamplingRate(250e6 / 4, 250e6, false), UsrpException);
    }
}

TEST_CASE("[ValidTxStreamingConfig]") {
    double guardOffset = 1.0;
    double fs = 20000.0;
    TxStreamingConfig prevConfig;
    prevConfig.samples = {{bi::samples_vec(2000, bi::sample(1.0, 1.0))}};

    TxStreamingConfig newConfig;
    newConfig.samples = {{}};
    SECTION("NewOffsetIsValid") {
        prevConfig.sendTimeOffset = 0.0;
        newConfig.sendTimeOffset = prevConfig.sendTimeOffset + guardOffset +
                                   prevConfig.samples[0].size() / fs;
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
        newConfig.sendTimeOffset = 1.0 + guardOffset / 2;
        REQUIRE_THROWS_AS(assertValidTxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }

    SECTION("NewOffsetSmallerThanDurationOfPreviousSignal") {
        prevConfig.sendTimeOffset = 1.0;
        newConfig.sendTimeOffset = 1.0 + guardOffset;
        REQUIRE_THROWS_AS(assertValidTxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }
}

TEST_CASE("TxStreamingConfig") {
    SECTION("Align to word size") {
        SECTION("zero length is already aligned") {
            MimoSignal samples{{}};
            TxStreamingConfig config(samples, 0);
            config.alignToWordSize();

            REQUIRE(config.samples[0].size() == 0);
        }

        SECTION("zeros are appended in MIMO") {
            MimoSignal samples{{1}, {2}};
            TxStreamingConfig config(samples, 0);
            config.alignToWordSize();

            REQUIRE(config.samples[0].size() == 8);
            REQUIRE(config.samples[1].size() == 8);
            REQUIRE(config.samples[0][0] == sample(1));
            REQUIRE(config.samples[1][0] == sample(2));

            for(int i = 1; i < 8; i++) {
                REQUIRE(config.samples[0][i] == sample(0));
                REQUIRE(config.samples[1][i] == sample(0));
            }
        }
    }
}

TEST_CASE("[ValidRxStreamingConfig]") {
    double guardOffset = 1.0;
    double fs = 20e6;
    RxStreamingConfig prevConfig;
    prevConfig.noSamples = 20e3;

    RxStreamingConfig newConfig;
    newConfig.noSamples = 20e3;
    SECTION("NewOffsetIsValid") {
        prevConfig.receiveTimeOffset = 0.0;
        newConfig.receiveTimeOffset = prevConfig.receiveTimeOffset +
                                      guardOffset + prevConfig.noSamples / fs;
        REQUIRE_NOTHROW(assertValidRxStreamingConfig(prevConfig, newConfig,
                                                     guardOffset, fs));
    }
    SECTION("NewOffsetSmallerThanPrevious") {
        prevConfig.receiveTimeOffset = 1.0;
        newConfig.receiveTimeOffset = 0.0;
        REQUIRE_THROWS_AS(assertValidRxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }

    SECTION("NewOffsetSmallerThanGuardOffset") {
        prevConfig.noSamples = 0;
        prevConfig.receiveTimeOffset = 1.0;
        newConfig.receiveTimeOffset = 1.0 + guardOffset / 2;
        REQUIRE_THROWS_AS(assertValidRxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }

    SECTION("NewOffsetSmallerThanDurationOfPreviousSignal") {
        prevConfig.receiveTimeOffset = 1.0;
        newConfig.receiveTimeOffset = 1.0 + guardOffset;
        REQUIRE_THROWS_AS(assertValidRxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }
    SECTION("UneventAmountOfSamples") {
        newConfig.noSamples = 199;
        REQUIRE_THROWS_AS(assertValidRxStreamingConfig(prevConfig, newConfig,
                                                       guardOffset, fs),
                          UsrpException);
    }
}

TEST_CASE("[ValidTxSignal]") {
    TxStreamingConfig conf;
    const size_t MAX_NUM_SAMPLES = (size_t)55e3;
    SECTION("SignalTooLong") {
        conf.samples = {samples_vec((size_t)56e3, sample(0, 0))};
        REQUIRE_THROWS_AS(assertValidTxSignal(conf.samples, MAX_NUM_SAMPLES,
                                              conf.samples.size()),
                          UsrpException);
    }
    SECTION("OneSignalTooLong_TheOtherAreFine") {
        conf.samples = {samples_vec((size_t)65e3, sample(0, 0)),
                        samples_vec(10, sample(0, 0))};
        REQUIRE_THROWS_AS(assertValidTxSignal(conf.samples, MAX_NUM_SAMPLES,
                                              conf.samples.size()),
                          UsrpException);
    }
    SECTION("SignalShorterThanMaxNumberSamples") {
        conf.samples = {samples_vec((size_t)10, sample(0, 0))};
        REQUIRE_NOTHROW(assertValidTxSignal(conf.samples, MAX_NUM_SAMPLES,
                                            conf.samples.size()));
    }

    SECTION("MimoSignalLengthsDiffer") {
        conf.samples = {samples_vec((size_t)100, sample(0, 0)),
                        samples_vec((size_t)200, sample(0.0))};
        REQUIRE_THROWS_AS(assertValidTxSignal(conf.samples, MAX_NUM_SAMPLES,
                                              conf.samples.size()),
                          UsrpException);
    }
    SECTION("NoTxSignalMismatchesNoTxAntennas") {
        conf.samples = {samples_vec((size_t)100, sample(0, 0)),
                        samples_vec((size_t)200, sample(0.0))};
        REQUIRE_THROWS_AS(
            assertValidTxSignal(conf.samples, MAX_NUM_SAMPLES, (size_t)1),
            UsrpException);
    }

    SECTION("NoSamplesProvided") {
        conf.samples = {};
        REQUIRE_THROWS_AS(
            assertValidTxSignal(conf.samples, MAX_NUM_SAMPLES, (size_t)1),
            UsrpException);
    }

    SECTION("UnevenAmountOfSamples") {
        conf.samples = {samples_vec((size_t)99, sample(0, 0))};
        REQUIRE_THROWS_AS(
            assertValidTxSignal(conf.samples, MAX_NUM_SAMPLES, (size_t)1),
            UsrpException);
    }

    SECTION("Forbid NAN values") {
        conf.samples = {{{NAN,0}, {0,1}, {0, 0}, {0, 1}}};
        REQUIRE_THROWS_AS(
                          assertValidTxSignal(conf.samples, MAX_NUM_SAMPLES, 1u),
                          UsrpException);
    }
}

TEST_CASE("[ValidRfConfig]") {
    RfConfig conf;
    SECTION("NoTxAntennasTooLarge") {
        conf.noTxAntennas = 5;
        REQUIRE_THROWS_AS(assertValidRfConfig(conf), UsrpException);
    }
    SECTION("NoRxAntennasTooLarge") {
        conf.noRxAntennas = 5;
        REQUIRE_THROWS_AS(assertValidRfConfig(conf), UsrpException);
    }

    SECTION("NoTxAntennasZero") {
        conf.noTxAntennas = 0;
        REQUIRE_THROWS_AS(assertValidRfConfig(conf), UsrpException);
    }
    SECTION("NoRxAntennasZero") {
        conf.noRxAntennas = 0;
        REQUIRE_THROWS_AS(assertValidRfConfig(conf), UsrpException);
    }
}

TEST_CASE("nextMultipleOfWordSize") {
    REQUIRE(nextMultipleOfWordSize(0) == 0);
    REQUIRE(nextMultipleOfWordSize(8) == 8);

    REQUIRE(nextMultipleOfWordSize(1) == 8);
    REQUIRE(nextMultipleOfWordSize(2) == 8);

    REQUIRE(nextMultipleOfWordSize(9) == 16);
    REQUIRE(nextMultipleOfWordSize(13) == 16);
    REQUIRE(nextMultipleOfWordSize(15) == 16);

    REQUIRE(nextMultipleOfWordSize(17) == 24);
}
}  // namespace bi
