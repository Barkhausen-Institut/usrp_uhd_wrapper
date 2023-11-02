#ifndef STREAM_MAPPER_H_
#define STREAM_MAPPER_H_

#include "rfnoc_blocks.hpp"

namespace bi {

class StreamMapperBase {
public:
    StreamMapperBase();

    virtual void configureRxAntenna(const RxStreamingConfig& rxConfig) = 0;

};

class StreamMapper : public StreamMapperBase, public RfNocBlocks {
public:
    StreamMapper(const RfNocBlockConfig& blockNames, uhd::rfnoc::rfnoc_graph::sptr graph);

    virtual void configureRxAntenna(const RxStreamingConfig& rxConfig);

};

}


#endif // STREAM_MAPPER_H_
