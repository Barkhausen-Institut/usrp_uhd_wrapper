#pragma once
#include "config.hpp"

enum ErrorCode { SUCCESS, FAILURE, MIMO_SPECIFICATION };
class UsrpInterface {
   public:
    virtual ErrorCode setRfConfig(const RfConfig&) = 0;
    virtual ErrorCode setTxConfig(std::shared_ptr<TxStreamingConfig>) = 0;
    virtual ErrorCode setRxConfig(std::shared_ptr<RxStreamingConfig>) = 0;
    virtual ErrorCode setTimeToZeroNextPps() = 0;
    virtual ErrorCode getCurrentTime(std::string&) = 0;
    virtual ErrorCode execute() = 0;
};
