cmake_minimum_required(VERSION 3.15)
project(usrp-uhd-wrapper)

find_package(UHD REQUIRED)

add_subdirectory(lib)
add_subdirectory(snippets)