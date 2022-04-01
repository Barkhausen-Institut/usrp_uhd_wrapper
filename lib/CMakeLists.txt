find_package(Boost COMPONENTS system thread program_options REQUIRED)

add_library(usrp usrp.cpp usrp_exception.cpp config.cpp)
target_link_libraries(usrp PRIVATE ${UHD_LIBRARIES} ${Boost_LIBRARIES} pthread)
target_include_directories(usrp PRIVATE ../include/)
