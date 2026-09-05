cmake_minimum_required(VERSION 3.22.1)
project("schoolaliascore")

add_library(schoolaliascore SHARED schoolalias_core.cpp)

find_library(log-lib log)
target_link_libraries(schoolaliascore ${log-lib})
