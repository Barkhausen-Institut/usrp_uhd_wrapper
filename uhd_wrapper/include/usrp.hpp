#pragma once
#include <sys/time.h>

#include <chrono>
#include <ctime>
#include <mutex>
#include <thread>

#include <uhd/rfnoc/block_id.hpp>
#include <uhd/rfnoc/radio_control.hpp>
#include <uhd/rfnoc/replay_block_control.hpp>
#include <uhd/rfnoc_graph.hpp>

#include "config.hpp"
#include "uhd/usrp/multi_usrp.hpp"
#include "usrp_exception.hpp"
#include "usrp_interface.hpp"

namespace bi {

class Usrp : public UsrpInterface {
   public:
    Usrp(const std::string& ip);
    ~Usrp();

    void setRfConfig(const RfConfig& rfConfig);
    void setTxConfig(const TxStreamingConfig& conf);
    void setRxConfig(const RxStreamingConfig& conf);
    void setTimeToZeroNextPps();
    uint64_t getCurrentSystemTime();
    double getCurrentFpgaTime();
    void execute(const double baseTime);
    std::vector<MimoSignal> collect();

    double getMasterClockRate() const { return masterClockRate_; }
    RfConfig getRfConfig() const;
    void resetStreamingConfigs();
    std::string getDeviceType() const;

   private:
    // RfNoC components
    uhd::rfnoc::rfnoc_graph::sptr graph_;
    uhd::rfnoc::block_id_t radioId1_, radioId2_;
    uhd::rfnoc::block_id_t replayId_;

    uhd::rfnoc::radio_control::sptr radioCtrl1_, radioCtrl2_;
    uhd::rfnoc::replay_block_control::sptr replayCtrl_;

    uhd::rx_streamer::sptr currentRxStreamer_;
    uhd::tx_streamer::sptr currentTxStreamer_;

    void createRfNocBlocks();
    typedef std::tuple<uhd::rfnoc::radio_control::sptr, int> RadioChannelPair;
    RadioChannelPair getRadioChannelPair(int antenna);

    void disconnectAll();
    void connectForUpload();
    void configureReplayForUpload(int numSamples);
    void performUpload(const MimoSignal& txSignal);

    void connectForStreaming();
    void configureReplayForStreaming(size_t numTxSamples, size_t numRxSamples);
    void performStreaming(double baseTime, size_t numTxSamples, size_t numRxSamples);

    void connectForDownload();
    void configureReplayForDownload(size_t numRxSamples);
    MimoSignal performDownload(size_t numRxSamples);

    // constants
    const double GUARD_OFFSET_S_ = 0.05;
    const size_t MAX_SAMPLES_TX_SIGNAL = (size_t)55e3;
    const std::vector<std::string> SUBDEV_SPECS = {
        "A:0", "A:0 A:1", "A:0 A:1 B:0", "A:0 A:1 B:0 B:1"};
    // variables
    uhd::usrp::multi_usrp::sptr usrpDevice_;
    std::string ip_;
    uhd::tx_streamer::sptr txStreamer_;
    uhd::rx_streamer::sptr rxStreamer_;
    std::vector<TxStreamingConfig> txStreamingConfigs_;
    std::vector<RxStreamingConfig> rxStreamingConfigs_;
    bool ppsSetToZero_ = false;
    std::thread transmitThread_;
    std::thread receiveThread_;
    mutable std::recursive_mutex fpgaAccessMutex_;
    std::thread setTimeToZeroNextPpsThread_;
    std::exception_ptr transmitThreadException_ = nullptr;
    std::exception_ptr receiveThreadException_ = nullptr;
    double masterClockRate_;
    RfConfig rfConfig_;

    std::vector<MimoSignal> receivedSamples_ = {{{}}};
    bool subdevSpecSet_ = false;

    // configuration functions
    void setTxSamplingRate(const double samplingRate,
                           const size_t txAntennaIdx);
    void setRxSamplingRate(const double samplingRate,
                           const size_t rxAntennaIdx);

    void setRfConfigForRxAntenna(const RfConfig& conf,
                                 const size_t rxAntennaIdx);
    void setRfConfigForTxAntenna(const RfConfig& conf,
                                 const size_t txAntennaIdx);

    void configureRxStreamer(const RfConfig& conf);
    void configureTxStreamer(const RfConfig& conf);

    // transmission related functions
    void transmit(const double baseTime, std::exception_ptr& exceptionPtr);
    void receive(const double baseTime, std::vector<MimoSignal>& buffers,
                 std::exception_ptr& exceptionPtr);
    void processRxStreamingConfig(const RxStreamingConfig& config,
                                  MimoSignal& buffer, const double baseTime);
    void processTxStreamingConfig(const TxStreamingConfig& config,
                                  const double baseTime);

    // remaining functions
    void setTimeToZeroNextPpsThreadFunction();
    void waitOnThreadToJoin(std::thread&);
};

}  // namespace bi
