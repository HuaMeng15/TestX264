cmake_minimum_required(VERSION 3.30)
project(test_libx264)

# target_compile_features(test_libx264 PRIVATE cxx_std_17)
set(CMAKE_CXX_STANDARD 17 CACHE STRING "v")
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_CXX_EXTENSIONS OFF)

# Add the source file
add_executable(test_libx264 test_x264.cpp)

# Set the path to libx264.a
set(LIBX264_LIBRARY "/Users/menghua/Research/x264/libx264.a")

# Set the path to x264.h
set(LIBX264_INCLUDE_DIR "/Users/menghua/Research/TestX264/include")

# Add the include directory
target_include_directories(test_libx264 PUBLIC ${LIBX264_INCLUDE_DIR})

# Link against libx264
target_link_libraries(test_libx264 ${LIBX264_LIBRARY})

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)