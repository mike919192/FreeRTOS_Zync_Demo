# Copyright (C) 2023 - 2024 Advanced Micro Devices, Inc.  All rights reserved.
# SPDX-License-Identifier: MIT
cmake_minimum_required(VERSION 3.16)

include(${CMAKE_CURRENT_SOURCE_DIR}/UserConfig.cmake)
set(APP_NAME rtos_test)
project(${APP_NAME})

find_package(common)
enable_language(C ASM CXX)
collect(PROJECT_LIB_DEPS xilstandalone;xiltimer;xilrsa)

#CPP STANDARD
set(CMAKE_CXX_STANDARD 20)

collect(PROJECT_LIB_DEPS xil)
collect(PROJECT_LIB_DEPS gcc)
collect(PROJECT_LIB_DEPS c)

# Use CMAKE_LIBRARY_PATH in link_directories
link_directories(${CMAKE_LIBRARY_PATH})

list(APPEND _sources ${USER_COMPILE_SOURCES})
foreach(source ${_sources})
    get_filename_component(ext ${source} EXT)
    list(APPEND src_ext ${ext})
endforeach()

if(NOT DEFINED PROJECT_TYPE)
    find_project_type("${src_ext}" PROJECT_TYPE)
endif()

if("${PROJECT_TYPE}" STREQUAL "c++")
    collect(PROJECT_LIB_DEPS stdc++)
    #set(CMAKE_C_COMPILER ${CMAKE_CXX_COMPILER})
endif()
collector_list(_deps PROJECT_LIB_DEPS)
list(APPEND _deps ${USER_LINK_LIBRARIES})

if("${PROJECT_TYPE}" STREQUAL "c++")
    string(REPLACE ";" ",-l" _deps "${_deps}")
endif()
if(CMAKE_EXPORT_COMPILE_COMMANDS AND (NOT ${YOCTO}))
    set(CMAKE_CXX_STANDARD_INCLUDE_DIRECTORIES
        ${CMAKE_CXX_IMPLICIT_INCLUDE_DIRECTORIES}
    )
    set(CMAKE_C_STANDARD_INCLUDE_DIRECTORIES
        ${CMAKE_C_IMPLICIT_INCLUDE_DIRECTORIES}
    )
endif()
linker_gen("${CMAKE_SOURCE_DIR}/linker_files/")
string(APPEND CMAKE_C_FLAGS ${USER_COMPILE_OPTIONS})
string(APPEND CMAKE_CXX_FLAGS ${USER_COMPILE_OPTIONS})
string(APPEND CMAKE_C_LINK_FLAGS ${USER_LINK_OPTIONS})
string(APPEND CMAKE_CXX_LINK_FLAGS ${USER_LINK_OPTIONS})

#ADD C ONLY FLAGS
string(
    APPEND
    CMAKE_C_FLAGS
    " -fmacro-prefix-map=${PROJECT_SOURCE_DIR}= -fmacro-prefix-map=${PROJECT_BINARY_DIR}/_deps="
)

#FETCH CONTENT HERE
include(FetchContent)

FetchContent_Declare(
    freertos_kernel
    GIT_REPOSITORY https://github.com/FreeRTOS/FreeRTOS-Kernel.git
    GIT_TAG V11.2.0
    # Don't grab any submodules
    GIT_SUBMODULES ""
)

add_library(freertos_config INTERFACE)

target_include_directories(freertos_config SYSTEM INTERFACE include)

target_compile_definitions(freertos_config INTERFACE projCOVERAGE_TEST=0)

set(FREERTOS_HEAP "4" CACHE STRING "" FORCE)
# Select the native compile PORT
#set( FREERTOS_PORT "GCC_POSIX" CACHE STRING "" FORCE)
# Select the cross-compile PORT
if(CMAKE_CROSSCOMPILING)
    set(FREERTOS_PORT "A_CUSTOM_PORT" CACHE STRING "" FORCE)
    target_compile_definitions(freertos_config INTERFACE ${definitions})
    target_compile_options(freertos_config INTERFACE ${options})
endif()

add_library(xil_bsp INTERFACE)
set_target_properties(xil_bsp PROPERTIES LINK_DEPENDS ${USER_LINKER_SCRIPT})
target_link_libraries(
    xil_bsp
    INTERFACE
        -Wl,-T
        -Wl,\"${USER_LINKER_SCRIPT}\"
        -L\"${CMAKE_SOURCE_DIR}/\"
        -L\"${CMAKE_LIBRARY_PATH}/\"
        -L\"${USER_LINK_DIRECTORIES}/\"
        -Wl,--start-group,-l${_deps}
        -Wl,--end-group
)
target_compile_definitions(xil_bsp INTERFACE ${USER_COMPILE_DEFINITIONS})
target_include_directories(xil_bsp INTERFACE ${USER_INCLUDE_DIRECTORIES})

add_subdirectory(external/FreeRTOS_Zynq_Port)

FetchContent_MakeAvailable(freertos_kernel)
#add_subdirectory(external/TraceRecorder)
#target_link_libraries(freertos_kernel_port INTERFACE trace_recorder)

# FetchContent_Declare(
#     freertos_plus_tcp
#     GIT_REPOSITORY https://github.com/FreeRTOS/FreeRTOS-Plus-TCP.git
#     #Note: Best practice to use specific git-hash or tagged version
#     GIT_TAG V4.3.3
#     # Don't grab any submodules since not latest
#     GIT_SUBMODULES ""
# )

# set(FREERTOS_PLUS_TCP_BUFFER_ALLOCATION "1" CACHE STRING "" FORCE)

# # Select the native compile PORT
# #set( FREERTOS_PLUS_TCP_NETWORK_IF "POSIX" CACHE STRING "" FORCE)
# # Or: select a cross-compile PORT
# if(CMAKE_CROSSCOMPILING)
#     # Eg. STM32Hxx version of port
#     set(FREERTOS_PLUS_TCP_NETWORK_IF
#         "A_CUSTOM_NETWORK_IF"
#         CACHE STRING
#         ""
#         FORCE
#     )
# endif()

# add_subdirectory(external/FreeRTOSTCP/Zynq)

# FetchContent_MakeAvailable(freertos_plus_tcp)

#ADD SUBDIRECTORIES HERE
# add_subdirectory(XXX)

if(NOT "${_sources}" STREQUAL "")
    add_dependency_on_bsp(_sources)
    add_executable(${APP_NAME}.elf ${_sources})
    set_target_properties(
        ${APP_NAME}.elf
        PROPERTIES LINK_DEPENDS ${USER_LINKER_SCRIPT}
    )

    # target_link_libraries(
    #     ${APP_NAME}.elf
    #     -Wl,-T
    #     -Wl,\"${USER_LINKER_SCRIPT}\"
    #     -L\"${CMAKE_SOURCE_DIR}/\"
    #     -L\"${CMAKE_LIBRARY_PATH}/\"
    #     -L\"${USER_LINK_DIRECTORIES}/\"
    #     -Wl,--start-group,-l${_deps}
    #     -Wl,--end-group
    # )

    #LINK LIBRARIES HERE    
    target_link_libraries(${APP_NAME}.elf freertos_kernel)

    target_compile_definitions(
        ${APP_NAME}.elf
        PUBLIC ${USER_COMPILE_DEFINITIONS}
    )
    target_include_directories(
        ${APP_NAME}.elf
        PUBLIC ${USER_INCLUDE_DIRECTORIES}
    )
    print_elf_size(CMAKE_SIZE ${APP_NAME})
endif()
