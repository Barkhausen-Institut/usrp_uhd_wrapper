#include <cmath>

#include "config.hpp"
#include "usrp_interface.hpp"
#include "utils.hpp"

std::vector<bi::samples_vec> createDummySamples(unsigned int noSamples) {
    std::vector<bi::samples_vec> samples;
    samples.emplace_back(zadoffChu(noSamples));

    return samples;
}
int main() {
    const unsigned int NO_TX_SAMPLES = 2000;
    const unsigned int NO_RX_SAMPLES = 60e3;

    std::string usrpIp = "localhost";
    std::shared_ptr<bi::UsrpInterface> usrpPtr = bi::createUsrp(usrpIp);
    bi::RfConfig rfConfig;
    rfConfig.txGain = 50;
    rfConfig.rxGain = 30;
    rfConfig.txCarrierFrequency = 2e9;
    rfConfig.rxCarrierFrequency = 2e9;
    rfConfig.txAnalogFilterBw = 400e6;
    rfConfig.rxAnalogFilterBw = 400e6;
    rfConfig.txSamplingRate = 122.88e6;
    rfConfig.rxSamplingRate = 122.88e6;

    bi::TxStreamingConfig txStreamingConfig;
    txStreamingConfig.samples = createDummySamples(NO_TX_SAMPLES);
    txStreamingConfig.sendTimeOffset = 1.5f;

    bi::RxStreamingConfig rxStreamingConfig;
    rxStreamingConfig.numSamples = NO_RX_SAMPLES;
    rxStreamingConfig.receiveTimeOffset = 1.5f;

    usrpPtr->setRfConfig(rfConfig);
    usrpPtr->setRfConfig(rfConfig);
    usrpPtr->setTxConfig(txStreamingConfig);
    usrpPtr->setRxConfig(rxStreamingConfig);
    bi::RfConfig conf = usrpPtr->getRfConfig();
    std::cout << conf << std::endl;
    /*std::cout << "Setting time to zero..." << std::endl;
    usrpPtr->setTimeToZeroNextPps();
    std::cout << "Current Time " << usrpPtr->getCurrentFpgaTime() << std::endl;
    usrpPtr->execute(0.f);
    std::vector<bi::MimoSignal> samples = usrpPtr->collect();
    std::ofstream csvFile = createCsv("rxSamples.csv", 1);
    dumpSamplesFirstConfig(samples[0], csvFile);*/
    return 0;
}
