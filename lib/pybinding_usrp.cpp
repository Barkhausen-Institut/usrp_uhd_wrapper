#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "usrp.hpp"

PYBIND11_MODULE(pymod, m) {
    // factory function
    m.def("createUsrp", bi::createUsrp);
}