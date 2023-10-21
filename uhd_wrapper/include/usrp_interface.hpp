#pragma once
#include <memory>

#include "config.hpp"

namespace bi {

class UsrpInterface {
   public:
    virtual ~UsrpInterface() {}
    virtual void setRfConfig(const RfConfig&) = 0;
    virtual void setTxConfig(const TxStreamingConfig& conf) = 0;
    virtual void setRxConfig(const RxStreamingConfig& conf) = 0;
    virtual void setSyncSource(const std::string& type) = 0;
    virtual void setTimeToZeroNextPps() = 0;

    virtual void execute(const double baseTime) = 0;
    virtual std::vector<MimoSignal> collect() = 0;
    virtual void resetStreamingConfigs() = 0;

    virtual uint64_t getCurrentSystemTime() = 0;
    virtual double getCurrentFpgaTime() = 0;
    virtual double getMasterClockRate() const = 0;
    virtual std::vector<double> getSupportedSampleRates() const = 0;
    virtual RfConfig getRfConfig() const = 0;
    virtual std::string getDeviceType() const = 0;
    virtual size_t getNumAntennas() const = 0;
};

std::unique_ptr<UsrpInterface> createUsrp(const std::string& ip);
}  // namespace bi
