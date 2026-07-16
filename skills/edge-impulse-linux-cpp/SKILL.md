---
name: edge-impulse-linux-cpp
description: Write C++ application code that uses a downloaded Edge Impulse C++ library on Linux. Use when asked to write a Linux runner, integrate the Edge Impulse SDK into a CMake project, or run inference on a Raspberry Pi or Jetson.
---

Write C++ applications that link against a downloaded Edge Impulse C++ library on Linux.

## Library layout

After extracting the .zip, the structure is:

    edge-impulse-sdk/
      edge-impulse-sdk/   # SDK source
      model-parameters/   # model weights and config
      tflite-model/       # TFLite flatbuffer
      CMakeLists.txt      # top-level build file

## Minimal CMakeLists.txt

    cmake_minimum_required(VERSION 3.13)
    project(ei_app)
    set(CMAKE_CXX_STANDARD 11)
    add_subdirectory(edge-impulse-sdk)
    add_executable(ei_app main.cpp)
    target_link_libraries(ei_app ei_sdk)

## Inference pattern

    #include "edge-impulse-sdk/classifier/ei_run_classifier.h"

    static float features[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];

    int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
        memcpy(out_ptr, features + offset, length * sizeof(float));
        return 0;
    }

    int main() {
        signal_t signal;
        signal.total_length = EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE;
        signal.get_data = &raw_feature_get_data;

        ei_impulse_result_t result;
        EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);
        if (err != EI_IMPULSE_OK) {
            printf("run_classifier failed: %d\n", err);
            return 1;
        }

        for (size_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
            printf("%s: %.4f\n", result.classification[i].label,
                                 result.classification[i].value);
        }
        return 0;
    }

## Build commands

    mkdir -p build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release
    make -j$(nproc)

## Instructions

1. Assume the library is extracted at ./build/edge-impulse-sdk. Do not re-download it.
2. Always use EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE for buffer sizing.
3. Ask the user what input source they are using (CSV file, live camera, microphone, etc.).
4. For camera input, use OpenCV to capture frames and convert to the expected format.
5. Target ARM64 by default unless the user specifies otherwise.
