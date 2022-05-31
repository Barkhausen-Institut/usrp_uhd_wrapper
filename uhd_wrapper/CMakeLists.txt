cmake_minimum_required(VERSION 3.15)
project(usrp-uhd-wrapper)
set(CMAKE_CXX_STANDARD 17) # required for trompeloeil and scoped_lock
set(PROJECT_3RD_PARTY_DIR ${CMAKE_SOURCE_DIR}/3rdparty)
add_compile_options(-Wall -Werror)

find_package(UHD REQUIRED)

add_subdirectory(3rdparty)
add_subdirectory(lib)
add_subdirectory(tests/cpp/)
add_subdirectory(snippets)
add_subdirectory(debug)

enable_testing()

install(FILES ${CMAKE_SOURCE_DIR}/../rpc-server.service DESTINATION /etc/systemd/system/)
