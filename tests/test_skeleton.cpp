/** @file
 *
 * This file serves to
 * 1. demonstrate how the catch file is to be included (without #define !) and
 * 2. to provide a test skeleton using catch2.
 **/

#include "catch/catch.hpp"

TEST_CASE("TestSkeleton", "[TestSkeleton]") {
  REQUIRE(1 == 1);
  REQUIRE(2 == 2);
}