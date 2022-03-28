#include "usrp.hpp"

ErrorCode Usrp::setRfConfig(const RfConfig& conf) {
    // init usrp
    ErrorCode retCode = SUCCESS;
    usrp_->set_tx_rate(conf.txSamplingRate);
    usrp_->set_rx_rate(conf.rxSamplingRate);

    return retCode;
}
