find_package(Boost COMPONENTS system thread program_options REQUIRED)

add_library(config config.cpp)
target_include_directories(config PRIVATE ../include/)

add_library(usrp usrp.cpp usrp_exception.cpp)
target_link_libraries(usrp PRIVATE ${UHD_LIBRARIES} ${Boost_LIBRARIES} pthread config)
target_include_directories(usrp PRIVATE ../include/)
