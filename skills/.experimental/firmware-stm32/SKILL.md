---
name: firmware-stm32
description: Integrate an exported Edge Impulse C++ library into STM32CubeIDE projects, including STM32H7 and FreeRTOS applications, sensor sampling, ISR-safe buffering, classifier tasks, linker and memory configuration, and STM32 SDK porting. Use when writing or debugging Edge Impulse inference firmware for STM32 microcontrollers.
metadata:
  version: "0.1.1"
---

# Edge Impulse on STM32

Integrate the complete C++ library exported from the project's Deployment page. Do not substitute a generic model or copy only the TFLite file.

## Inspect first

1. Identify the STM32 part, CubeIDE/CubeMX version, RTOS use, sensor and bus, model input type, sample interval, and RAM/flash limits.
2. Inspect the export for `edge-impulse-sdk/`, `model-parameters/`, `tflite-model/`, and the generated inferencing header.
3. Inspect the existing project's source groups, include paths, linker script, cache setup, and RTOS heap before editing.

## Integrate the library

1. Copy the exported SDK, model parameters, and model sources into a dedicated project directory.
2. Add all required C/C++ sources and include paths. Compile inference callers as C++.
3. Include the generated project header when present; otherwise include:

```cpp
#include "edge-impulse-sdk/classifier/ei_run_classifier.h"
```

4. Select the STM32/CMSIS porting implementation included by the export. Do not compile POSIX or other platform ports.
5. Enable CMSIS-DSP/CMSIS-NN only when the target and exported deployment support them.
6. Resolve duplicate runtime, allocator, or CMSIS sources rather than suppressing linker errors.

## Sample safely with FreeRTOS

Use a producer/consumer design:

- A timer or data-ready ISR records the minimum required state and wakes a sampling task, or places a completed nonblocking sample into a static queue.
- Perform SPI/I2C transactions in a task unless the exact HAL operation is documented as ISR-safe and nonblocking.
- The ISR uses only ISR-safe RTOS APIs and `portYIELD_FROM_ISR` when needed.
- An inference task waits for a complete window, snapshots it, creates `signal_t`, and calls `run_classifier()`.
- Never call `run_classifier()`, allocate memory, log extensively, or block inside an ISR.

Size buffers from generated constants:

```cpp
static float features[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];

static int get_signal_data(size_t offset, size_t length, float *out) {
    memcpy(out, features + offset, length * sizeof(float));
    return EIDSP_OK;
}
```

Collect samples at `EI_CLASSIFIER_INTERVAL_MS` and preserve the axis/channel order used during training. For an SPI IIS2DH, configure the data rate and full-scale range explicitly, read coherent XYZ samples, convert to the same units as training, and avoid blocking HAL SPI transfers in an interrupt handler.

## Run inference

```cpp
signal_t signal{};
signal.total_length = EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE;
signal.get_data = get_signal_data;

ei_impulse_result_t result{};
EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);
if (err != EI_IMPULSE_OK) {
    // Report or count the error outside interrupt context.
}
```

Handle classification, object detection, and anomaly outputs according to the generated macros. Do not assume only classification output.

## Memory and timing

- Place large static buffers in an appropriate SRAM region and update the linker script deliberately.
- On cache-enabled STM32H7 parts, maintain cache coherency for DMA buffers and use correctly aligned memory.
- Measure stack high-water marks, heap use, DSP time, inference time, and missed samples.
- If memory is tight, use static allocation options supported by the exported SDK and reduce logging before changing the model.

## Verify

1. First run a copied Studio test window and compare scores within expected floating-point tolerance.
2. Then test live sensor input, checking sample interval, units, axis order, and buffer completeness.
3. Run long enough to detect stack overflow, queue overrun, timing drift, or DMA/cache faults.
4. Perform a clean CubeIDE rebuild before reporting success.

## Documentation

- https://docs.edgeimpulse.com/hardware/deployments/run-cubemx — run a Cube.MX CMSIS-Pack deployment in STM32 projects
- https://docs.edgeimpulse.com/hardware/boards/stm32n6570-dk — STM32N6570-DK board guide

## Reference repositories

- https://github.com/edgeimpulse/example-standalone-inferencing-stm32h747i-disco — standalone inferencing on the STM32H747I-DISCO
- https://github.com/edgeimpulse/firmware-st-stm32n6 — official ingestion and inferencing firmware for the STM32N6570-DK
- https://github.com/edgeimpulse/example-standalone-st-stm32n6 — standalone inferencing for the STM32N6570-DK

Other toolchains (not CubeIDE):

- https://github.com/edgeimpulse/example-standalone-inferencing-stm32f4-csolution — STM32F4 Nucleo using the CMSIS toolbox
- https://github.com/edgeimpulse/example-standalone-inferencing-st-nucleo-f466re — Nucleo F466RE using Keil MDK
