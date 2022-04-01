#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "usrp_interface.hpp"

namespace py = pybind11;
PYBIND11_MODULE(pymod, m) {
    // factory function
    m.def("createUsrp", &bi::createUsrp, "Creates a USRP with dedicated IP.");

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
    py::class_<bi::UsrpInterface>(m, "Usrp").def(
        "setRfConfig", &bi::UsrpInterface::setRfConfig);
}