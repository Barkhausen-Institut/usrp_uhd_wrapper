pybind11_add_module(usrp_pybinding usrp_pybinding/usrp.cpp)
target_link_libraries(usrp_pybinding PRIVATE usrp)
target_include_directories(usrp_pybinding PRIVATE ../include/)

add_library(usrp STATIC usrp.cpp usrp_exception.cpp config.cpp)
target_link_libraries(usrp PRIVATE ${UHD_LIBRARIES} ${Boost_LIBRARIES} pthread)
target_include_directories(usrp PRIVATE ../include/)
set_property(TARGET usrp PROPERTY POSITION_INDEPENDENT_CODE ON)

install (TARGETS usrp_pybinding DESTINATION ${CMAKE_SOURCE_DIR})