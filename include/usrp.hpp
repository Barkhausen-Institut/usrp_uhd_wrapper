#pragma once
#include <sys/time.h>
#include <chrono>
#include <ctime>
#include <thread>

#include "uhd/usrp/multi_usrp.hpp"

#include "config.hpp"
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
    }
    void setRfConfig(const RfConfig& rfConfig);
    void setTxConfig(const TxStreamingConfig& conf);
    void setRxConfig(const RxStreamingConfig& conf);
    void setTimeToZeroNextPps();
    uint64_t getCurrentSystemTime();
    double getCurrentFpgaTime();
    std::vector<samples_vec> execute(const float baseTime);

   private:
    // variables
    uhd::usrp::multi_usrp::sptr usrpDevice_;
    std::string ip_;
    uhd::tx_streamer::sptr txStreamer_;
    std::vector<TxStreamingConfig> txStreamingConfigs_;
    std::vector<RxStreamingConfig> rxStreamingConfigs_;
    bool ppsSetToZero_;

    // functions
    void transmit(const float baseTime);
};
}  // namespace bi
