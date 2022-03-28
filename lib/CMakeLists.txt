find_package(UHD REQUIRED)

add_library(usrp usrp.cpp)
target_link_libraries(usrp PRIVATE ${UHD_LIBRARIES})
target_include_directories(usrp PRIVATE ../include/)