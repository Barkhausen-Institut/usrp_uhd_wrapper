cmake_minimum_required(VERSION 3.16)
project(usrp-uhd-wrapper)

find_package(UHD REQUIRED)
add_subdirectory(lib SHARED)
add_subdirectory(snippets)