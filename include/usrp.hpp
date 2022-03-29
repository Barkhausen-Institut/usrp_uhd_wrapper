#pragma once
#include "uhd/usrp/multi_usrp.hpp"

#include "config.hpp"
#include "usrp_interface.hpp"

class Usrp : public UsrpInterface {
   public:
    Usrp(const std::string& ip) {
        ip_ = ip;
        usrp_ = uhd::usrp::multi_usrp::make(uhd::device_addr_t(ip));

        uhd::stream_args_t txStreamArgs("fc32", "sc16");
        txStreamArgs.channels = std::vector<size_t>({0});
        txStreamer_ = usrp_->get_tx_stream(txStreamArgs);
    }
    ErrorCode setRfConfig(const RfConfig& rfConfig);
    ErrorCode setTxConfig(const TxStreamingConfig& conf);
    ErrorCode setRxConfig(const RxStreamingConfig& conf);
    ErrorCode setTimeToZeroNextPps();
    ErrorCode getCurrentTime(std::string&){};
    ErrorCode execute(){};

   private:
    // variables
    uhd::usrp::multi_usrp::sptr usrp_;
    std::string ip_;
    uhd::tx_streamer::sptr txStreamer_;
    std::vector<TxStreamingConfig> txStreamingConfigs_;
    std::vector<RxStreamingConfig> rxStreamingConfigs_;
};