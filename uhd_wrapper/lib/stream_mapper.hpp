#ifndef STREAM_MAPPER_H_
#define STREAM_MAPPER_H_

#include "rfnoc_blocks.hpp"

namespace bi {

class StreamMapperBase {
public:
    StreamMapperBase();

    virtual void configureRxAntenna(const RxStreamingConfig& rxConfig) = 0;

    void setRfConfig(const RfConfig& config);
    void applyDefaultMapping(int numStreams);
    uint mapTxStreamToAntenna(uint streamIdx) const;
    uint mapRxStreamToAntenna(uint streamIdx) const;

private:
    typedef std::vector<int> Mapping;
    Mapping txMapping_;
    Mapping rxMapping_;

    uint mapStreamToAntenna(uint streamIdx, const Mapping& mapping) const;
    Mapping defaultMapping(uint numStreams) const;
    void checkMapping(const Mapping& mapping, uint numStreams);

};

class StreamMapper : public StreamMapperBase, public RfNocBlocks {
public:
    StreamMapper(const RfNocBlockConfig& blockNames, uhd::rfnoc::rfnoc_graph::sptr graph);

    virtual void configureRxAntenna(const RxStreamingConfig& rxConfig);

private:
    std::string defaultRxPort_;
    std::string calculateDefaultRxPort();

};

}


#endif // STREAM_MAPPER_H_
