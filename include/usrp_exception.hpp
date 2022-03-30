#pragma once

#include <stdexcept>

namespace bi {
class UsrpException : public std::runtime_error {
   public:
    UsrpException(const char*) throw();
    const char* what() const throw();

   private:
    const char* errorMessage_;
};
}  // namespace bi