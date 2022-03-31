
# compile catch_main as a library once and link it to each test_executable
# do not touch!
add_library(CatchMain catch_main.cpp)
target_include_directories(CatchMain PUBLIC ${PROJECT_3RD_PARTY_DIR})

# #############################
# add your tests here
include(CTest)
add_executable(unittests test_config.cpp ) # put other test_*.cpp files here
target_link_libraries(unittests CatchMain) # no need to touch this
target_include_directories(unittests PRIVATE ../include/)
add_test(NAME unittests COMMAND ${CMAKE_CURRENT_BINARY_DIR}/unittests) # don't touch this either