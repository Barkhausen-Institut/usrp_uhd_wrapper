#pragma once
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <complex>
#include <memory>

#include "config.hpp"
namespace py = pybind11;
namespace bi {

std::shared_ptr<std::vector<samples_vec>> takeVectorOfArrays(
    const std::vector<py::array_t<sample>>& signals);
}  // namespace bi