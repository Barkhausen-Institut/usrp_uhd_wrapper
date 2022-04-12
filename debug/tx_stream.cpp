#include <csignal>
#include <random>

#include "config.hpp"
#include "usrp.hpp"

static bool stopSignal = false;
void sig_int_handler(int) { stopSignal = true; }

const size_t SPB = 2000;
bi::samples_vec createNoise(const double mean, const double std) {
    // Define random generator with Gaussian distribution
    std::default_random_engine generator;
    std::normal_distribution<double> dist(mean, std);

    bi::samples_vec noise(SPB, bi::sample(0, 0));
    // Add Gaussian noises
    for (bi::sample &x : noise) {
        x.real(dist(generator));
        x.imag(dist(generator));
    }

    return noise;
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

    bi::samples_vec signal;
    while (not stopSignal) {
        signal = createNoise(0, 2);
        txStreamer->send({signal.data()}, SPB, mdTx, 0.1f);
        mdTx.start_of_burst = false;
    }
    mdTx.end_of_burst = true;
    txStreamer->send("", 0, mdTx);
    // we need to introduce this sleep to ensure that the samples have
    // already been sent since the buffering is non-blocking inside the
    // thread. If we close the the outer scope before the samples are
    // actually sent, they will not be sent any more out of the FPGA.
    std::this_thread::sleep_for(
        std::chrono::milliseconds(static_cast<int>(1000 * timeOffset)));
}

void setRfConfig(const bi::RfConfig &conf,
                 uhd::usrp::multi_usrp::sptr usrpDevice) {
    // configure transmitter
    usrpDevice->set_tx_rate(conf.txSamplingRate);
    usrpDevice->set_tx_subdev_spec(uhd::usrp::subdev_spec_t("A:0"), 0);
    uhd::tune_request_t txTuneRequest(conf.txCarrierFrequency[0]);
    usrpDevice->set_tx_freq(txTuneRequest, 0);
    usrpDevice->set_tx_gain(conf.txGain[0], 0);
    usrpDevice->set_tx_bandwidth(conf.txAnalogFilterBw, 0);
}
int main() {
    std::signal(SIGINT, &sig_int_handler);

    bi::RfConfig rfConfig;
    rfConfig.txGain = {50};
    rfConfig.txCarrierFrequency = {2e9};
    rfConfig.txAnalogFilterBw = 400e6;
    rfConfig.txSamplingRate = 10e6;
    uhd::usrp::multi_usrp::sptr usrpDevice =
        uhd::usrp::multi_usrp::make(uhd::device_addr_t("addr=localhost"));

    setRfConfig(rfConfig, usrpDevice);
    uhd::stream_args_t txStreamArgs("fc32", "sc16");
    txStreamArgs.channels = std::vector<size_t>({0});
    uhd::tx_streamer::sptr txStreamer = usrpDevice->get_tx_stream(txStreamArgs);

    std::thread transmitThread(transmit, 2.0, txStreamer);
    stopSignal = true;
    transmitThread.join();
}