---
name: firmware-cpp
description: Write C++ application code that uses a downloaded Edge Impulse C++ library, covering both the portable "C++ library" and the hardware-accelerated "C++ library (Linux)" Studio deployment options. Use for desktop or Linux applications, CMake integration, or porting the library into a generic MCU or custom C++ build system. For Arduino, STM32CubeIDE, or Zephyr targets, prefer the dedicated firmware-arduino, firmware-stm32, and firmware-zephyr skills.
metadata:
  version: "0.1.1"
---

Write C++ applications that use a downloaded Edge Impulse C++ library on desktop, Linux, or generic MCU targets.

## Choose the export

Studio offers two C++ deployment options. Confirm which one the user downloaded before writing build instructions:

- **C++ library** — portable, no external dependencies, compiles with any modern C++ compiler. Use for desktop apps, generic MCU integration, and CMake projects. No hardware acceleration.
- **C++ library (Linux)** — same portable library plus full hardware acceleration on Linux (full TensorFlow Lite and target-specific optimizations). Prefer it for Raspberry Pi, Jetson, and other Linux SBCs, and build it with the `example-standalone-inferencing-linux` harness rather than a hand-written CMakeLists.

## Library layout (portable export)

After extracting the .zip, the structure is:

    edge-impulse-sdk/
      edge-impulse-sdk/   # SDK source
      model-parameters/   # model weights and config
      tflite-model/       # TFLite flatbuffer
      CMakeLists.txt      # top-level build file

## Minimal CMakeLists.txt (portable export, desktop)

    cmake_minimum_required(VERSION 3.13)
    project(ei_app)
    set(CMAKE_CXX_STANDARD 11)
    add_subdirectory(edge-impulse-sdk)
    add_executable(ei_app main.cpp)
    target_link_libraries(ei_app ei_sdk)

Build:

    mkdir -p build && cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release
    make -j$(nproc)

## Linux export with hardware acceleration

Use the `example-standalone-inferencing-linux` repository as the build harness: clone it, initialize its submodules, and unzip the Linux C++ export into it. Select the application and target with Make flags:

    # custom sensor data, generic build
    APP_CUSTOM=1 make -j$(nproc)

    # hardware-accelerated builds
    APP_CUSTOM=1 TARGET_LINUX_AARCH64=1 USE_FULL_TFLITE=1 make -j$(nproc)
    APP_CUSTOM=1 TARGET_LINUX_X86=1 USE_FULL_TFLITE=1 make -j$(nproc)

- Applications: `APP_CUSTOM=1` (custom sensor data), `APP_AUDIO=1` (realtime audio), `APP_CAMERA=1` (realtime camera), `APP_EIM=1` (build an .eim for the Python, Node.js, or Go SDKs).
- Audio requires libasound2; the camera app requires OpenCV (build scripts are included in the repo).
- Jetson and other accelerated targets have dedicated `TARGET_*` flags; check the repo README for the current list before guessing one.

## Inference pattern

The inference API is identical on every target:

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

## Generic MCU and custom build systems

When the target has no CMake support, integrate the portable library into the existing build system instead of using the top-level CMakeLists.txt:

1. Add the `edge-impulse-sdk/`, `model-parameters/`, and `tflite-model/` sources and include paths to the project's build. Compile inference callers as C++11 or later.
2. Select exactly one porting layer from `edge-impulse-sdk/porting/` that matches the target. For an unsupported target, implement the porting functions (`ei_printf`, `ei_read_timer_ms`, `ei_read_timer_us`, `ei_sleep`, and the `ei_malloc`/`ei_calloc`/`ei_free` family) for the platform. Never compile more than one porting implementation.
3. Keep the features buffer static and size it with `EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE`; verify the target has enough RAM and flash for the model before debugging anything else.
4. Call `run_classifier()` from a task or main-loop context, never from an interrupt handler.

## Instructions

1. Assume the library is extracted at ./build/edge-impulse-sdk. Do not re-download it.
2. Determine which export the user has: if the target is a Linux SBC and hardware acceleration matters, expect the **C++ library (Linux)** export and the Make-based harness; otherwise expect the portable **C++ library** export.
3. Always use EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE for buffer sizing.
4. Ask the user what platform they are targeting (desktop, Linux SBC, or MCU) and what input source they are using (CSV file, live camera, microphone, sensor, etc.) if not specified.
5. For camera input on desktop or Linux, use OpenCV to capture frames and convert to the expected format.
6. On desktop, build for the native architecture. For Linux SBCs, target ARM64 by default unless the user specifies otherwise.
7. For Arduino, STM32CubeIDE, or Zephyr projects, use the dedicated firmware-arduino, firmware-stm32, or firmware-zephyr skill instead of this generic integration.

## Documentation

- https://docs.edgeimpulse.com/hardware/deployments/run-cpp — run the C++ library on custom boards
- https://docs.edgeimpulse.com/hardware/deployments/run-cpp-desktop — run the C++ library on desktop
- https://docs.edgeimpulse.com/tools/libraries/sdks/inference/linux/cpp — Linux C++ SDK (hardware-accelerated export)
- https://docs.edgeimpulse.com/tools/libraries/sdks/inference/cpp — C++ inferencing SDK API reference

## Reference repositories

- https://github.com/edgeimpulse/example-standalone-inferencing-linux — build harness for the Linux export with camera, audio, and .eim applications
- https://github.com/edgeimpulse/example-standalone-inferencing-cmake — barebones CMake example matching the pattern above
- https://github.com/edgeimpulse/example-standalone-inferencing — minimal Make-based desktop example for the portable export (no hardware optimization)
- https://github.com/edgeimpulse/example-standalone-inferencing-with-library — linking against a prebuilt static or shared Edge Impulse library
- https://github.com/edgeimpulse/inferencing-sdk-cpp — source of the portable C++ inferencing SDK
