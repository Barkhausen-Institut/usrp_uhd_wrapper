/** @file
 *
 * This file serves to
 * 1. demonstrate how the catch file is to be included (without #define !) and
 * 2. to provide a test skeleton using catch2.
 **/

#include "catch/catch.hpp"
#include "config.hpp"

namespace bi {
TEST_CASE("[SamplesDoNotFitEvenlyIntoBuffer]") {
    int noSamples = 0;
    int spb = 0;
    SECTION("No samples in last package") {
        noSamples = 4000;
        spb = 2000;
        REQUIRE(calcNoPackages(noSamples, spb) == 2);
        REQUIRE(calcNoSamplesLastBuffer(noSamples, spb) == 2000);
    }
    SECTION("Ten samples in last package") {
        noSamples = 4010;
        spb = 2000;
        REQUIRE(calcNoPackages(noSamples, spb) == 3);
        REQUIRE(calcNoSamplesLastBuffer(noSamples, spb) == 10);
    }
}
}  // namespace bi