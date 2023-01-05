#pragma once
#include <sys/time.h>

#include <chrono>
#include <ctime>
#include <mutex>
#include <thread>

#include <uhd/rfnoc/block_id.hpp>
#include <uhd/rfnoc/radio_control.hpp>
#include <uhd/rfnoc/replay_block_control.hpp>
#include <uhd/rfnoc/duc_block_control.hpp>
#include <uhd/rfnoc/ddc_block_control.hpp>
#include <uhd/rfnoc_graph.hpp>

#include "config.hpp"
#include "usrp_interface.hpp"

#include "full_duplex_rfnoc_graph.hpp"
#include "rf_configuration.hpp"

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

    double getMasterClockRate() const;
    RfConfig getRfConfig() const;
    void resetStreamingConfigs();
    std::string getDeviceType() const;

   private:
    std::shared_ptr<RfNocFullDuplexGraph> fdGraph_;
    std::shared_ptr<RFConfiguration> rfConfig_;
    // RfNoC components
    uhd::rfnoc::rfnoc_graph::sptr graph_;
    uhd::rfnoc::block_id_t replayId_;

    uhd::rfnoc::replay_block_control::sptr replayCtrl_;

    void createRfNocBlocks();

    void configureReplayForUpload(int numSamples);
    void performUpload(const MimoSignal& txSignal);

    void configureReplayForStreaming(size_t numTxSamples, size_t numRxSamples);
    void performStreaming(double baseTime, size_t numTxSamples, size_t numRxSamples);

    void configureReplayForDownload(size_t numRxSamples);
    MimoSignal performDownload(size_t numRxSamples);

    void clearReplayBlockRecorder();

    // constants
    const double GUARD_OFFSET_S_ = 0.05;
    const size_t MAX_SAMPLES_TX_SIGNAL = (size_t)55e3;
    const size_t PACKET_SIZE = 8192;

    // variables
    std::string ip_;
    std::vector<TxStreamingConfig> txStreamingConfigs_;
    std::vector<RxStreamingConfig> rxStreamingConfigs_;
    bool ppsSetToZero_ = false;
    std::thread transmitThread_;
    std::thread receiveThread_;
    mutable std::recursive_mutex fpgaAccessMutex_;
    std::thread setTimeToZeroNextPpsThread_;
    std::exception_ptr transmitThreadException_ = nullptr;
    std::exception_ptr receiveThreadException_ = nullptr;

    std::vector<MimoSignal> receivedSamples_ = {{{}}};

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
