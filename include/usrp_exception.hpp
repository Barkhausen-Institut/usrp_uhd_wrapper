#pragma once

#include <stdexcept>

namespace bi {
class UsrpException : public std::runtime_error {
   public:
    using std::runtime_error::runtime_error;
};
}  // namespace bi