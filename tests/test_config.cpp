/** @file
 *
 * This file serves to
 * 1. demonstrate how the catch file is to be included (without #define !) and
 * 2. to provide a test skeleton using catch2.
 **/

#include "catch/catch.hpp"
#include "config.hpp"

TEST_CASE("full first package and ten samples in second package",
          "[ZeroPadding]") {
    const size_t SAMPLES_PER_BUFFER = 30;
    bi::samples_vec samples =
        bi::samples_vec(SAMPLES_PER_BUFFER + 10, bi::sample(1, 1));
}