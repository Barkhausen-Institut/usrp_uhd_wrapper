#include "config.hpp"
#include "usrp.hpp"
#include "usrp_interface.hpp"
int main() {
    std::string usrpIp = "localhost";
    Usrp usrp(usrpIp);
    RfConfig rfConfig;
    rfConfig.txGain = 40;
    rfConfig.rxGain = 30;
    rfConfig.txCarrierFrequency = 2e9;
    rfConfig.rxCarrierFrequency = 2e9;
    rfConfig.txAnalogFilterBw = 400e6;
    rfConfig.rxAnalogFilterBw = 400e6;
    rfConfig.txSamplingRate = 200e6;
    rfConfig.rxSamplingRate = 200e6;
    usrp.setRfConfig(rfConfig);
}
