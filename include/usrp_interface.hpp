#pragma once
#include <memory>

#include "config.hpp"

namespace bi {
class UsrpInterface {
   public:
    virtual void setRfConfig(const RfConfig&) = 0;
    virtual void setTxConfig(const TxStreamingConfig& conf) = 0;
    virtual void setRxConfig(const RxStreamingConfig& conf) = 0;
    virtual void setTimeToZeroNextPps() = 0;
    virtual uint64_t getCurrentSystemTime() = 0;
    virtual double getCurrentFpgaTime() = 0;
    virtual std::vector<samples_vec> execute(const float baseTime) = 0;
    virtual void reset() = 0;
    virtual double getMasterClockRate() const = 0;

   protected:
    virtual void setTxSamplingRate(const double samplingRate) = 0;
    virtual void setRxSamplingRate(const double samplingRate) = 0;
};

std::unique_ptr<UsrpInterface> createUsrp(const std::string& ip);
}  // namespace bi
