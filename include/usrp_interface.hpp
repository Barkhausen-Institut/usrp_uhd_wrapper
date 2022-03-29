#pragma once
#include <memory>
#include "config.hpp"

class UsrpInterface {
   public:
    virtual void setRfConfig(const RfConfig&) = 0;
    virtual void setTxConfig(const TxStreamingConfig& conf) = 0;
    virtual void setRxConfig(const RxStreamingConfig& conf) = 0;
    virtual void setTimeToZeroNextPps() = 0;
    virtual void getCurrentTime(std::string&) = 0;
    virtual std::vector<package> execute() = 0;
};

std::shared_ptr<UsrpInterface> createUsrp(std::string ip);
