#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "usrp_interface.hpp"

PYBIND11_MODULE(pymod, m) {
    // factory function
    m.def("createUsrp", &bi::createUsrp, "Creates a USRP with dedicated IP.");

    // wrap object
    pybind11::class_<bi::UsrpInterface>(m, "Usrp");
}