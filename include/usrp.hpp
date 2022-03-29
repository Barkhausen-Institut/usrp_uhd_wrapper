#pragma once
#include <sys/time.h>
#include <chrono>
#include <ctime>
#include "uhd/usrp/multi_usrp.hpp"

#include "config.hpp"
#include "usrp_interface.hpp"

class Usrp : public UsrpInterface {
   public:
    Usrp(const std::string& ip) {
        ip_ = ip;
        usrp_ = uhd::usrp::multi_usrp::make(uhd::device_addr_t("addr=" + ip));
    }
    void setRfConfig(const RfConfig& rfConfig);
    void setTxConfig(const TxStreamingConfig& conf);
    void setRxConfig(const RxStreamingConfig& conf);
    void setTimeToZeroNextPps();
    uint64_t getCurrentTime();
    std::vector<package> execute(){};

   private:
    // variables
    uhd::usrp::multi_usrp::sptr usrp_;
    std::string ip_;
    uhd::tx_streamer::sptr txStreamer_;
    std::vector<TxStreamingConfig> txStreamingConfigs_;
    std::vector<RxStreamingConfig> rxStreamingConfigs_;
};
