#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "usrp_interface.hpp"

namespace py = pybind11;

namespace bi {

std::vector<py::array_t<bi::sample>> returnVectorOfArrays(
    const std::vector<bi::samples_vec>& samplesIn) {
    std::vector<py::array_t<sample>> samplesOut;
    for (auto& v : samplesIn) {
        samplesOut.emplace_back(
            py::array_t<sample>({(py::ssize_t)v.size()}, v.data()));
    }

    return samplesOut;
}

std::vector<samples_vec> takeVectorOfArrays(
    const std::vector<py::array_t<sample>>& signals) {
    std::vector<samples_vec> vectorOfSamplesVec;

    for (auto& s : signals) {
        vectorOfSamplesVec.emplace_back(s.data(), s.data() + s.shape(0));
    }
    return vectorOfSamplesVec;
}
}  // namespace bi

PYBIND11_MODULE(usrp_pybinding, m) {
    // factory function
    m.def("createUsrp", &bi::createUsrp);

    // wrap object
    py::class_<bi::RfConfig>(m, "RfConfig")
        .def(py::init())
        .def_readwrite("txSamplingRate", &bi::RfConfig::txSamplingRate)
        .def_readwrite("rxSamplingRate", &bi::RfConfig::rxSamplingRate)
        .def_readwrite("txAnalogFilterBw", &bi::RfConfig::txAnalogFilterBw)
        .def_readwrite("rxAnalogFilterBw", &bi::RfConfig::rxAnalogFilterBw)
        .def_readwrite("txGain", &bi::RfConfig::txGain)
        .def_readwrite("rxGain", &bi::RfConfig::rxGain)
        .def_readwrite("txCarrierFrequency", &bi::RfConfig::txCarrierFrequency)
        .def_readwrite("rxCarrierFrequency", &bi::RfConfig::rxCarrierFrequency);

    py::class_<bi::RxStreamingConfig>(m, "RxStreamingConfig")
        .def(py::init())
        .def_readwrite("noSamples", &bi::RxStreamingConfig::noSamples)
        .def_readwrite("receiveTimeOffset",
                       &bi::RxStreamingConfig::receiveTimeOffset);

    py::class_<bi::TxStreamingConfig>(m, "TxStreamingConfig")
        .def(py::init())
        .def(py::init(
                 [](std::vector<py::array_t<bi::sample>>& s, const float o) {
                     auto c = std::make_unique<bi::TxStreamingConfig>();
                     c->samples = bi::takeVectorOfArrays(s);
                     c->sendTimeOffset = o;
                     return c;
                 }),
             py::arg("samples"), py::arg("sendTimeOffset"))

        .def_property(
            "samples",
            [](bi::TxStreamingConfig& c) {
                return bi::returnVectorOfArrays(c.samples);
            },
            [](bi::TxStreamingConfig& c,
               const std::vector<py::array_t<bi::sample>>& samples) {
                c.samples = bi::takeVectorOfArrays(samples);
            })
        .def_readwrite("sendTimeOffset",
                       &bi::TxStreamingConfig::sendTimeOffset);
    py::class_<bi::UsrpInterface>(m, "Usrp")
        .def("setRfConfig", &bi::UsrpInterface::setRfConfig)
        .def("setRxConfig", &bi::UsrpInterface::setRxConfig)
        .def("setTxConfig", &bi::UsrpInterface::setTxConfig)
        .def("setTimeToZeroNextPps", &bi::UsrpInterface::setTimeToZeroNextPps)
        .def("getCurrentSystemTime", &bi::UsrpInterface::getCurrentSystemTime)
        .def("getCurrentFpgaTime", &bi::UsrpInterface::getCurrentFpgaTime)
        .def("execute",
             [](bi::UsrpInterface& u, const float baseTime) {
                 return bi::returnVectorOfArrays(u.execute(baseTime));
             })
        .def("reset", &bi::UsrpInterface::reset);
}