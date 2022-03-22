cmake_minimum_required(VERSION 3.10)
project("InsertProjectHere")
#########################################################
# define paths here
#########################################################
set(PROJECT_3RD_PARTY_DIR ${CMAKE_SOURCE_DIR}/3rdparty)

#########################################################
# perform testing
#########################################################
enable_testing()
add_subdirectory(tests)
#add_subdirectory(src)

include(bi_boilerplate.cmake)
