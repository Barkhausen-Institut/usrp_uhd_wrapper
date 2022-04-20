add_executable(tx_stream tx_stream.cpp)
target_include_directories(tx_stream PRIVATE ../include)
target_link_libraries(tx_stream PRIVATE ${UHD_LIBRARIES} pthread)