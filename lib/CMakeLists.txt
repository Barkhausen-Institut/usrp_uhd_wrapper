find_package(Boost COMPONENTS system thread program_options REQUIRED)

add_library(usrp_exception usrp_exception.cpp)
target_include_directories(usrp_exception PRIVATE ../include/)

add_library(usrp usrp.cpp)
target_link_libraries(usrp PRIVATE ${UHD_LIBRARIES} ${Boost_LIBRARIES} pthread usrp_exception)
target_include_directories(usrp PRIVATE ../include/)