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
        txStreamArgs.channels = std::vector<int>({0});
        txStreamer_ = usrp_->get_tx_stream(txStreamArgs);

        mdTx_.start_of_burst = true;
        mdTx_.end_of_burst = false;
        mdTx_.has_time_spec = true;
    }
    ErrorCode setRfConfig(const RfConfig& rfConfig);
    ErrorCode setTxConfig(const TxStreamingConfig& conf);

   private:
    // methods
    void defineMimoSetup(const RfConfig& conf);

    // variables
    uhd::usrp::multi_usrp::sptr usrp_;
    std::string ip_;
    uhd::tx_streamer::sptr txStreamer_;
    uhd::tx_metadata_t mdTx_;
};