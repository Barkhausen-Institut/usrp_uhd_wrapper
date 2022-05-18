#pragma once
#include <sys/time.h>

#include <chrono>
#include <ctime>
#include <mutex>
#include <thread>

#include "config.hpp"
#include "uhd/usrp/multi_usrp.hpp"
#include "usrp_exception.hpp"
#include "usrp_interface.hpp"

namespace bi {

class Usrp : public UsrpInterface {
   public:
    Usrp(const std::string& ip) {
        ip_ = ip;
        usrpDevice_ =
            uhd::usrp::multi_usrp::make(uhd::device_addr_t("addr=" + ip));
        usrpDevice_->set_sync_source("external", "external");
        masterClockRate_ = usrpDevice_->get_master_clock_rate();
    }
    ~Usrp() { usrpDevice_->set_sync_source("internal", "internal"); }
    void setRfConfig(const RfConfig& rfConfig);
    void setTxConfig(const TxStreamingConfig& conf);
    void setRxConfig(const RxStreamingConfig& conf);
    void setTimeToZeroNextPps();
    uint64_t getCurrentSystemTime();
    double getCurrentFpgaTime();
    void execute(const double baseTime);
    std::vector<MimoSignal> collect();

    double getMasterClockRate() const { return masterClockRate_; }
    RfConfig getRfConfig() const;
    void resetStreamingConfigs();

   private:
    // constants
    const double GUARD_OFFSET_S_ = 0.05;
    const size_t MAX_SAMPLES_TX_SIGNAL = (size_t)64e3;
    const std::vector<std::string> SUBDEV_SPECS = {
        "A:0", "A:0 A:1", "A:0 A:1 B:0", "A:0 A:1 B:0 B:1"};
    // variables
    uhd::usrp::multi_usrp::sptr usrpDevice_;
    std::string ip_;
    uhd::tx_streamer::sptr txStreamer_;
    uhd::rx_streamer::sptr rxStreamer_;
    std::vector<TxStreamingConfig> txStreamingConfigs_;
    std::vector<RxStreamingConfig> rxStreamingConfigs_;
    bool ppsSetToZero_ = false;
    std::thread transmitThread_;
    std::thread receiveThread_;
    mutable std::recursive_mutex fpgaAccessMutex_;
    std::thread setTimeToZeroNextPpsThread_;
    std::exception_ptr transmitThreadException_ = nullptr;
    std::exception_ptr receiveThreadException_ = nullptr;
    double masterClockRate_;
    RfConfig rfConfig_;

    std::vector<MimoSignal> receivedSamples_ = {{{}}};
    bool subdevSpecSet_ = false;

    // functions
    void setTxSamplingRate(const double samplingRate);
    void setRxSamplingRate(const double samplingRate, size_t rxAntennaIdx);

    void setRfConfigForRxAntenna(const RfConfig& conf, size_t rxAntennaIdx);
    void transmit(const double baseTime, std::exception_ptr& exceptionPtr);
    void receive(const double baseTime, std::vector<MimoSignal>& buffers,
                 std::exception_ptr& exceptionPtr);
    void setTimeToZeroNextPpsThreadFunction();
    void processRxStreamingConfig(const RxStreamingConfig& config,
                                  MimoSignal& buffer, const double baseTime);
    void processTxStreamingConfig(const TxStreamingConfig& config,
                                  const double baseTime);
};

}  // namespace bi
