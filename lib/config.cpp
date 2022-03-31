#include "config.hpp"
namespace bi {
size_t calcNoPackages(const size_t noSamples, const size_t spb) {
    return std::ceil(noSamples / spb);
}
size_t calcNoSamplesLastBuffer(const size_t noSamples, const size_t spb) {
    size_t noSamplesLastBuffer = noSamples % SAMPLES_PER_BUFFER;
    if (noSamplesLastBuffer == 0) noSamplesLastBuffer = SAMPLES_PER_BUFFER;
    return noSamplesLastBuffer;
}
}  // namespace bi