#include "usrp_exception.hpp"

namespace bi {
UsrpException::UsrpException(const char* msg) throw()
    : std::runtime_error(msg) {}
const char* UsrpException::what() const throw() { return errorMessage_; }
}  // namespace bi