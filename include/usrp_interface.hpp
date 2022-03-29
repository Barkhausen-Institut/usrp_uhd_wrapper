#pragma once
#include <memory>
#include "config.hpp"

enum ErrorCode { SUCCESS, FAILURE };
class UsrpInterface {
   public:
    virtual ErrorCode setRfConfig(const RfConfig&) = 0;
    virtual ErrorCode setTxConfig(const TxStreamingConfig& conf) = 0;
    virtual ErrorCode setRxConfig(const RxStreamingConfig& conf) = 0;
    virtual ErrorCode setTimeToZeroNextPps() = 0;
    virtual ErrorCode getCurrentTime(std::string&) = 0;
    virtual ErrorCode execute() = 0;
};

std::shared_ptr<UsrpInterface> createUsrp(std::string ip);
