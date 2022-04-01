find_package(Boost COMPONENTS system thread program_options REQUIRED)
pybind11_add_module(pymod pybinding/usrp.cpp)
target_link_libraries(pymod PRIVATE usrp)
target_include_directories(pymod PRIVATE ../include/)

add_library(usrp STATIC usrp.cpp usrp_exception.cpp config.cpp)
target_link_libraries(usrp PRIVATE ${UHD_LIBRARIES} ${Boost_LIBRARIES} pthread)
target_include_directories(usrp PRIVATE ../include/)
set_property(TARGET usrp PROPERTY POSITION_INDEPENDENT_CODE ON)

