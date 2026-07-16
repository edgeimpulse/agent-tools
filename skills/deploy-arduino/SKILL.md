---
name: deploy-arduino
description: Write Arduino application code that uses a downloaded Edge Impulse library. Use when asked to write a sketch, integrate an Edge Impulse model into Arduino code, or run inference on an Arduino board.
metadata:
  version: "1.0.0"
---

Write Arduino sketches that use a downloaded Edge Impulse Arduino library.

## Library structure

The downloaded .zip contains an Arduino library. The main header follows the pattern:

    #include <PROJECT_SLUG_inferencing.h>

where PROJECT_SLUG is derived from the project name. Find the exact header name
by listing the extracted library directory:

    find ./build -name '*_inferencing.h' 2>/dev/null | head -1

Use whatever filename that command returns — do not guess or hardcode it.

## Inference pattern

    #include <PROJECT_SLUG_inferencing.h>   // use the actual filename found above

    float features[EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE];

    int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
        memcpy(out_ptr, features + offset, length * sizeof(float));
        return 0;
    }

    void loop() {
        // Fill features[] with sensor readings here

        signal_t signal;
        numpy::signal_from_buffer(features, EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE, &signal);

        ei_impulse_result_t result;
        EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);
        if (err != EI_IMPULSE_OK) {
            Serial.print("run_classifier failed: "); Serial.println(err);
            return;
        }

        for (size_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
            Serial.print(result.classification[i].label);
            Serial.print(": ");
            Serial.println(result.classification[i].value, 4);
        }
    }

## Key constants defined by the library

- EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE — total floats needed for one inference window
- EI_CLASSIFIER_LABEL_COUNT — number of output classes
- EI_CLASSIFIER_INTERVAL_MS — sampling interval in milliseconds

## Instructions

1. Before writing any code, run `find ./build -name '*_inferencing.h' 2>/dev/null | head -1`
   to find the exact header filename. Use that name in the #include — do not guess.
2. Use EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE for buffer sizing — never hardcode the number.
3. Collect sensor data at EI_CLASSIFIER_INTERVAL_MS intervals.
4. Ask the user which sensor they are using (IMU, microphone, or camera) if not specified.
5. Use the Arduino Wire, SPI, or sensor-specific libraries appropriate for the board.
