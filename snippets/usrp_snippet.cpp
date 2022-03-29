#include "config.hpp"
#include "usrp_interface.hpp"
int main() {
    std::string usrpIp = "localhost";
    std::shared_ptr<bi::UsrpInterface> usrpPtr = bi::createUsrp(usrpIp);
    bi::RfConfig rfConfig;
    rfConfig.txGain = 40;
    rfConfig.rxGain = 30;
    rfConfig.txCarrierFrequency = 2e9;
    rfConfig.rxCarrierFrequency = 2e9;
    rfConfig.txAnalogFilterBw = 400e6;
    rfConfig.rxAnalogFilterBw = 400e6;
    rfConfig.txSamplingRate = 200e6;
    rfConfig.rxSamplingRate = 200e6;
    usrpPtr->setRfConfig(rfConfig);
}
