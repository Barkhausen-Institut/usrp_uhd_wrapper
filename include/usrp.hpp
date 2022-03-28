#pragma once
#include "uhd/usrp/multi_usrp.hpp"

#include "config.hpp"
#include "usrp_interface.hpp"

class Usrp : public UsrpInterface {
   public:
    Usrp(const std::string& ip) {
        ip_ = ip;
        usrp_ = uhd::usrp::multi_usrp::make(uhd::device_addr_t(ip));
    }
    ErrorCode setRfConfig(const RfConfig& rfConfig);

   private:
    uhd::usrp::multi_usrp::sptr usrp_;
    std::string ip_;
};