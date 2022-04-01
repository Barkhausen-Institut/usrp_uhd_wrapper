#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "pybinding/usrp.hpp"
#include "usrp_interface.hpp"

namespace py = pybind11;

namespace bi {
std::shared_ptr<std::vector<samples_vec>> takeVectorOfArrays(
    const std::vector<py::array_t<sample>>& signals) {
    auto vectorOfSamplesVec = std::make_shared<std::vector<samples_vec>>();

    for (auto& s : signals) {
        vectorOfSamplesVec->emplace_back(s.data(), s.data() + s.shape(0));
    }
    return vectorOfSamplesVec;
}
}  // namespace bi

PYBIND11_MODULE(pymod, m) {
    // factory function
    m.def("createUsrp", &bi::createUsrp, return_value_policy::take_ownership);

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

    py::class_<bi::RxStreamingConfig>(m, "RxStreamingConfig") {
        .def(py::init())
            .def_readwrite("noSamples", &bi::RxStreamingConfig::noSamples)
            .def_readwrite("receiveTimeOffset",
                           &bi::RxStreamingConfig::receiveTimeOffset);
    }
    py::class_<bi::UsrpInterface>(m, "Usrp")
        .def("setRfConfig", &bi::UsrpInterface::setRfConfig)
        .def("setRxConfig", &bi::UsrpInterface::setRxConfig)
        .def("setTimeToZeroNextPps", &bi::UsrpInterface::setTimeToZeroNextPps)
        .def("getCurrentSystemTime", &bi::UsrpInterface::getCurrentSystemTime)
        .def("getCurrentFpgaTime", &bi::UsrpInterface::getCurrentFpgaTime)
        .def("execute", &bi::UsrpInterface::execute);
}