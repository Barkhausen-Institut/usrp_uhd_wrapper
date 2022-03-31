#pragma once
#include <complex>
#include <fstream>
#include <iostream>
#include <vector>

#include "config.hpp"

void dumpSamples(const std::vector<bi::samples_vec> &samples,
                 std::ofstream &stream) {
    size_t noChannels = samples.size();
    for (size_t chIdx = 0; chIdx < noChannels; chIdx++) {
        for (size_t sampleIdx = 0; sampleIdx < samples[chIdx].size();
             sampleIdx++) {
            const std::complex<float> &sample = samples[chIdx][sampleIdx];

            stream << sample.real() << "," << sample.imag();
            if (chIdx < noChannels - 1) stream << ",";
            stream << std::endl;
        }
    }
}

std::ofstream createCsv(const std::string &filename, const size_t noChannels) {
    std::cout << "Storing samples to " << filename << std::endl;
    std::ofstream csv_stream(filename);
    for (size_t chIdx = 0; chIdx < noChannels; chIdx++) {
        csv_stream << "real_ch" << chIdx << ",imag_ch" << chIdx;
        if (chIdx < noChannels - 1) {
            csv_stream << ",";
        }
    }
    csv_stream << std::endl;
    return csv_stream;
}
