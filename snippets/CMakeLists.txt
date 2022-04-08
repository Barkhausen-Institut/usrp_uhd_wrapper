add_executable(usrp_snippet usrp_snippet.cpp)
target_link_libraries(usrp_snippet PUBLIC usrp)
target_include_directories(usrp_snippet PRIVATE ../include/)
