#pragma once
#include <sys/time.h>

#include <chrono>
#include <ctime>
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
        ppsSetToZero_ = false;
        usrpDevice_->set_sync_source("external", "external");
    }
    void setRfConfig(const RfConfig& rfConfig);
    void setTxConfig(const TxStreamingConfig& conf);
    void setRxConfig(const RxStreamingConfig& conf);
    void setTimeToZeroNextPps();
    uint64_t getCurrentSystemTime();
    double getCurrentFpgaTime();
    void execute(const float baseTime);
    std::vector<samples_vec> collect() { return {{}}; }
    void reset();

   private:
    // variables
    uhd::usrp::multi_usrp::sptr usrpDevice_;
    std::string ip_;
    uhd::tx_streamer::sptr txStreamer_;
    uhd::rx_streamer::sptr rxStreamer_;
    std::vector<TxStreamingConfig> txStreamingConfigs_;
    std::vector<RxStreamingConfig> rxStreamingConfigs_;
    bool ppsSetToZero_;
    std::thread transmitThread_;
    // functions
    void transmit(const float baseTime, std::exception_ptr& exceptionPtr,
                  const double fpgaTimeThreadStart);
    void receive(const float baseTime, std::vector<samples_vec>& buffer,
                 std::exception_ptr& exceptionPtr,
                 const double fpgaTimeThreadStart);
};

}  // namespace bi
