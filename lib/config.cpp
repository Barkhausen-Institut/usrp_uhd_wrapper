#include <cmath>
#include "config.hpp"
namespace bi {
size_t calcNoPackages(const size_t noSamples, const size_t spb) {
    // taken from
    // https://stackoverflow.com/questions/2745074/fast-ceiling-of-an-integer-division-in-c-c
    return (noSamples + spb - 1) / spb;
}
size_t calcNoSamplesLastBuffer(const size_t noSamples, const size_t spb) {
    size_t noSamplesLastBuffer = noSamples % spb;
    if (noSamplesLastBuffer == 0) noSamplesLastBuffer = spb;
    return noSamplesLastBuffer;
}
}  // namespace bi