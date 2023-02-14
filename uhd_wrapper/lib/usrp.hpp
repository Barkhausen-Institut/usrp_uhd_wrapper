#pragma once
#include <sys/time.h>

#include <chrono>
#include <ctime>
#include <mutex>
#include <thread>

#include <uhd/rfnoc/block_id.hpp>
#include <uhd/rfnoc/replay_block_control.hpp>
#include <uhd/rfnoc_graph.hpp>

#include "config.hpp"
#include "usrp_interface.hpp"

#include "full_duplex_rfnoc_graph.hpp"
#include "rf_configuration.hpp"
#include "replay_config.hpp"

namespace bi {

class Usrp : public UsrpInterface {
   public:
    Usrp(const std::string& ip);
    ~Usrp();

    void setRfConfig(const RfConfig& rfConfig) override;
    void setTxConfig(const TxStreamingConfig& conf) override;
    void setRxConfig(const RxStreamingConfig& conf) override;
    void setSyncSource(const std::string& type) override;

    void setTimeToZeroNextPps() override;
    uint64_t getCurrentSystemTime() override;
    double getCurrentFpgaTime() override;
    void execute(const double baseTime) override;
    std::vector<MimoSignal> collect() override;


    double getMasterClockRate() const override;
    RfConfig getRfConfig() const override;
    void resetStreamingConfigs() override;
    std::string getDeviceType() const override;

   private:
    // RfNoC components
    uhd::rfnoc::rfnoc_graph::sptr graph_;
    std::shared_ptr<RfNocFullDuplexGraph> fdGraph_;
    std::shared_ptr<RFConfiguration> rfConfig_;
    std::shared_ptr<ReplayBlockConfig> replayConfig_;


    void createRfNocBlocks();

    void performUpload();
    void performStreaming(double baseTime);
    void performDownload();

    // constants
    const double GUARD_OFFSET_S_ = 0.05;
    const size_t MAX_SAMPLES_TX_SIGNAL = (size_t)200e3;
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
