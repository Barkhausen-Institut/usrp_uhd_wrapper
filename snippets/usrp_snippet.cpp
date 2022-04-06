#include "config.hpp"
#include "usrp_interface.hpp"

std::vector<bi::samples_vec> createDummySamples() {
    std::vector<bi::samples_vec> samples;
    bi::samples_vec frameAnt1 = bi::samples_vec(63.5e3, bi::sample(3, 3));
    samples.push_back(frameAnt1);
    return samples;
}
int main() {
    std::string usrpIp = "localhost";
    std::shared_ptr<bi::UsrpInterface> usrpPtr = bi::createUsrp(usrpIp);
    bi::RfConfig rfConfig;
    rfConfig.txGain = {50};
    rfConfig.rxGain = {30};
    rfConfig.txCarrierFrequency = {2e9};
    rfConfig.rxCarrierFrequency = {2e9};
    rfConfig.txAnalogFilterBw = 400e6;
    rfConfig.rxAnalogFilterBw = 400e6;
    rfConfig.txSamplingRate = 10e6;
    rfConfig.rxSamplingRate = 10e6;

    bi::TxStreamingConfig txStreamingConfig;
    txStreamingConfig.samples = createDummySamples();
    txStreamingConfig.sendTimeOffset = 1.5f;
    usrpPtr->setRfConfig(rfConfig);
    usrpPtr->setTxConfig(txStreamingConfig);
    std::vector<bi::samples_vec> samples = usrpPtr->execute(0.f);
}
