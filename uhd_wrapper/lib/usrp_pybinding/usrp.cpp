#include <pybind11/numpy.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>

#include "usrp_exception.hpp"
#include "usrp_interface.hpp"

namespace py = pybind11;

typedef std::vector<py::array_t<bi::sample>> NumpyMimoSignal;

namespace bi {

NumpyMimoSignal toNumpyMimoSignal(const MimoSignal& samplesIn) {
    NumpyMimoSignal samplesOut;
    for (auto& v : samplesIn) {
        samplesOut.emplace_back(
            py::array_t<sample>({(py::ssize_t)v.size()}, v.data()));
    }

    return samplesOut;
}

MimoSignal fromNumpyMimoSignal(const NumpyMimoSignal& signals) {
    MimoSignal result;

    for (auto& s : signals) {
        result.emplace_back(s.data(), s.data() + s.shape(0));
    }
    return result;
}

}  // namespace bi

// Custom class to convert bi::MimoSignal to / from Python. In Python
// it is represented as a list of numpy arrays.
// adapted from
// https://pybind11.readthedocs.io/en/stable/advanced/cast/custom.html
namespace pybind11 {
namespace detail {
template<>
struct type_caster<bi::MimoSignal> {
   public:
    /**
     * This macro establishes the name 'MimoSignal' in
     * function signatures and declares a local variable
     * 'value' of type MimoSignal
     */
    PYBIND11_TYPE_CASTER(bi::MimoSignal, const_name("MimoSignal"));

    /**
     * Conversion part 1 (Python->C++):          */
    bool load(handle src, bool convert) {
        NumpyMimoSignal temp;
        for (const auto& elem : src.cast<py::list>()) {
            temp.push_back(elem.cast<py::array_t<bi::sample>>());
        }
        value = bi::fromNumpyMimoSignal(temp);
        return true;
    }

    /**
     * Conversion part 2 (C++ -> Python):          */
    static handle cast(const bi::MimoSignal& src,
                       return_value_policy /* policy */, handle /* parent */) {
        NumpyMimoSignal x = bi::toNumpyMimoSignal(src);
        auto result = py::cast(x);
        result.inc_ref();
        return result;
    }
};
}  // namespace detail
}  // namespace pybind11

PYBIND11_MODULE(usrp_pybinding, m) {
    // factory function
    m.def("createUsrp", &bi::createUsrp);
    m.def("assertSamplingRate", &bi::assertSamplingRate);

    // wrap object
    py::class_<bi::RfConfig>(m, "RfConfig")
        .def(py::init())
        .def(py::init<const float, const float, const float, const float,
                      const float, const float, const float, const float,
                      const int, const int>(),
             py::arg("txGain"), py::arg("rxGain"),
             py::arg("rxCarrierFrequency"), py::arg("txCarrierFrequency"),
             py::arg("txAnalogFilterBw"), py::arg("rxAnalogFilterBw"),
             py::arg("txSamplingRate"), py::arg("rxSamplingRate"),
             py::arg("noRxAntennas"), py::arg("noTxAntennas"))
        .def_readwrite("txSamplingRate", &bi::RfConfig::txSamplingRate)
        .def_readwrite("rxSamplingRate", &bi::RfConfig::rxSamplingRate)
        .def_readwrite("txAnalogFilterBw", &bi::RfConfig::txAnalogFilterBw)
        .def_readwrite("rxAnalogFilterBw", &bi::RfConfig::rxAnalogFilterBw)
        .def_readwrite("txGain", &bi::RfConfig::txGain)
        .def_readwrite("rxGain", &bi::RfConfig::rxGain)
        .def_readwrite("txCarrierFrequency", &bi::RfConfig::txCarrierFrequency)
        .def_readwrite("rxCarrierFrequency", &bi::RfConfig::rxCarrierFrequency)
        .def_readwrite("noRxAntennas", &bi::RfConfig::noRxAntennas)
        .def_readwrite("noTxAntennas", &bi::RfConfig::noTxAntennas)
        .def(py::self == py::self);

    py::class_<bi::RxStreamingConfig>(m, "RxStreamingConfig")
        .def(py::init())
        .def(py::init<const unsigned int, const double>(), py::arg("noSamples"),
             py::arg("receiveTimeOffset"))
        .def_readwrite("noSamples", &bi::RxStreamingConfig::noSamples)
        .def_readwrite("receiveTimeOffset",
                       &bi::RxStreamingConfig::receiveTimeOffset)
        .def(py::self == py::self);

    py::class_<bi::TxStreamingConfig>(m, "TxStreamingConfig")
        .def(py::init())
        .def(py::init<const bi::MimoSignal&, const double>(),
             py::arg("samples"), py::arg("sendTimeOffset"))
        .def_readwrite("samples", &bi::TxStreamingConfig::samples)
        .def_readwrite("sendTimeOffset", &bi::TxStreamingConfig::sendTimeOffset)
        .def(py::self == py::self);

    py::class_<bi::UsrpInterface>(m, "Usrp")
        .def("setRfConfig", &bi::UsrpInterface::setRfConfig)
        .def("setRxConfig", &bi::UsrpInterface::setRxConfig)
        .def("setTxConfig", &bi::UsrpInterface::setTxConfig)
        .def("setTimeToZeroNextPps", &bi::UsrpInterface::setTimeToZeroNextPps)
        .def("getCurrentSystemTime", &bi::UsrpInterface::getCurrentSystemTime)
        .def("getCurrentFpgaTime", &bi::UsrpInterface::getCurrentFpgaTime)
        .def("execute", &bi::UsrpInterface::execute)
        .def("collect", &bi::UsrpInterface::collect)
        .def("resetStreamingConfigs", &bi::UsrpInterface::resetStreamingConfigs)
        .def("getMasterClockRate", &bi::UsrpInterface::getMasterClockRate)
        .def("getRfConfig", &bi::UsrpInterface::getRfConfig)
        .def_property_readonly("deviceType", &bi::UsrpInterface::getDeviceType);

    // takes a MimoSignal as the parameter from Python and creates a
    // streaming config with it. Used only for testing
    m.def("_createTxConfig",
          [](const bi::MimoSignal& signal, float sendTimeOffset) {
              return bi::TxStreamingConfig(signal, sendTimeOffset);
          });

    // return hard-coded vector of MimoSignal, to test if the to-python
    // conversion works with compound types. Used only for testing
    m.def("_returnVectorOfMimoSignals", []() {
        return std::vector<bi::MimoSignal>{{{1, 2, 3, 4}, {5, 6, 7, 8}}};
    });
}
