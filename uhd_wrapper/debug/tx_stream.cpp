#include <csignal>
#include <random>

#include "config.hpp"
#include "usrp.hpp"

static bool stopSignal = false;
void sig_int_handler(int) { stopSignal = true; }

const size_t SPB = 2000;
void createNoise(bi::samples_vec &noise, std::normal_distribution<double> &dist,
                 std::default_random_engine &generator) {
    // Add Gaussian noises
    for (bi::sample &x : noise) {
        x.real(dist(generator));
        x.imag(dist(generator));
    }
}
void transmit(const float timeOffset, uhd::tx_streamer::sptr txStreamer) {
    // assume one txStreamConfig for the moment....
    // add helpers

    // specifiy on specifications of how to stream the command
    uhd::tx_metadata_t mdTx;
    mdTx.start_of_burst = true;
    mdTx.end_of_burst = false;
    mdTx.has_time_spec = true;

    // double fpgaTimeBeforeSending = getCurrentFpgaTime();
    mdTx.time_spec = uhd::time_spec_t(timeOffset);

    bi::samples_vec signal(SPB, bi::sample(0, 0));
    // Define random generator with Gaussian distribution
    std::default_random_engine generator;
    std::normal_distribution<double> dist(0, 2);
    createNoise(signal, dist, generator);

    uhd::ref_vector<const void *> samplesRefVector = {signal.data()};
    while (not stopSignal) {
        txStreamer->send(samplesRefVector, SPB, mdTx, 0.3f);
        mdTx.start_of_burst = false;
        mdTx.has_time_spec = false;
    }
    mdTx.end_of_burst = true;
    txStreamer->send("", 0, mdTx);
}

void setRfConfig(const bi::RfConfig &conf,
                 uhd::usrp::multi_usrp::sptr usrpDevice) {
    // configure transmitter
    usrpDevice->set_tx_rate(conf.txSamplingRate[0]);
    usrpDevice->set_tx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
    uhd::tune_request_t txTuneRequest(conf.txCarrierFrequency[0]);
    usrpDevice->set_tx_freq(txTuneRequest, 0);
    usrpDevice->set_tx_gain(conf.txGain[0], 0);
    usrpDevice->set_tx_bandwidth(conf.txAnalogFilterBw[0], 0);
}
int main() {
    std::signal(SIGINT, &sig_int_handler);

    bi::RfConfig rfConfig;
    rfConfig.txGain = {30};
    rfConfig.txCarrierFrequency = {2e9};
    rfConfig.txAnalogFilterBw = {400e6};
    rfConfig.txSamplingRate = {50e6};
    uhd::usrp::multi_usrp::sptr usrpDevice =
        uhd::usrp::multi_usrp::make(uhd::device_addr_t("addr=localhost"));

    setRfConfig(rfConfig, usrpDevice);
    uhd::stream_args_t txStreamArgs("fc32", "sc16");
    txStreamArgs.channels = std::vector<size_t>({0});
    uhd::tx_streamer::sptr txStreamer = usrpDevice->get_tx_stream(txStreamArgs);
    usrpDevice->set_time_next_pps(0.f);
    std::thread transmitThread(transmit, 3.0, txStreamer);
    transmitThread.join();
    stopSignal = true;
    return 0;
}