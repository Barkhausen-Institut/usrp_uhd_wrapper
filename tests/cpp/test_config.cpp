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
}  // namespace bi