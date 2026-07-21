---
name: firmware-raspberry-pi-python
description: Run Edge Impulse EIM models on Raspberry Pi and other Linux systems with the edge_impulse_linux Python SDK. Use when building Python inference loops for custom sensors, images, video, USB microphones, audio classification, keyword spotting, or when debugging ImpulseRunner and AudioImpulseRunner applications.
metadata:
  version: "0.1.1"
---

# Edge Impulse Python on Raspberry Pi

Use the official `edge_impulse_linux` package with a Linux EIM executable built for the Pi's architecture. Do not pass an Arduino library, raw TFLite file, or EIM built for another architecture.

## Set up

For Raspberry Pi OS:

```bash
sudo apt install libatlas-base-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
python3 -m pip install edge_impulse_linux pyaudio
chmod +x model.eim
```

Keep dependencies in the project's virtual environment when possible. Verify the microphone with ALSA tools before debugging Python.

## Choose the runner

- Use `ImpulseRunner` for custom numeric data, images, and general models.
- Use `AudioImpulseRunner` for streaming audio and keyword spotting.
- Use the official SDK image examples as the starting point for camera color conversion, resizing, and feature packing.

Always initialize the runner, inspect `model_info`, and close it in `finally` or a context manager. Model metadata is the source of truth for frequency, frame size, labels, and input shape.

## General runner pattern

```python
from edge_impulse_linux.runner import ImpulseRunner

runner = ImpulseRunner("model.eim")
try:
    model_info = runner.init()
    # Build one feature window in the exact training order and units.
    features = []
    result = runner.classify(features)
    print(result["result"])
finally:
    runner.stop()
```

Check the installed SDK version's method signatures before finalizing code. The SDK and examples are canonical when an API differs from this pattern.

## USB microphone workflow

1. Enumerate PyAudio devices and select the intended input device explicitly.
2. Read the model frequency and window requirements from `model_info`.
3. Configure mono PCM with the required sample rate; convert samples exactly as the SDK example expects.
4. Use `AudioImpulseRunner` to maintain the rolling audio window and continuous classifier state.
5. Handle input overflow by fixing buffering or device configuration, not by silently discarding arbitrary chunks.
6. Separate inference callbacks from slow network, UI, or file work so audio capture remains timely.

Do not resample unless necessary. If resampling is required, use a deterministic library and verify its output rate and dtype.

## Results

Support the model's actual output:

- Classification and keyword spotting: inspect label scores and apply a user-defined threshold and debounce/cooldown policy.
- Object detection: iterate nonzero bounding boxes.
- Anomaly: report the anomaly score when present.

Do not assume scores sum to one for every model type.

## Troubleshoot

- Use `runner.init(debug=True)` to surface EIM logs.
- For very large models, increase the `ImpulseRunner(..., timeout=SECONDS)` timeout deliberately.
- If initialization fails, verify executable permission, CPU architecture, deployment target, and shared-library dependencies.
- If predictions differ from Studio, compare one identical raw feature window before debugging live capture.
- For audio errors, verify ALSA/PulseAudio/PipeWire routing, sample format, channels, rate, and device ownership.

## Verify

1. Run a known Studio sample through the local pipeline.
2. Compare the scores and preprocessing assumptions.
3. Exercise continuous capture for several minutes while checking memory, latency, dropped frames, and clean shutdown.

## Documentation

- https://docs.edgeimpulse.com/tools/libraries/sdks/inference/linux/python — Linux Python SDK
- https://docs.edgeimpulse.com/hardware/deployments/run-linux-eim — Linux EIM deployment
- https://docs.edgeimpulse.com/tools/clis/edge-impulse-linux-cli — Edge Impulse Linux CLI

## Reference repositories

- https://github.com/edgeimpulse/linux-sdk-python — source of `edge_impulse_linux` and the canonical runner examples
- https://github.com/edgeimpulse/edge-impulse-linux-cli — Linux CLI used to download and run EIM models
- https://github.com/edgeimpulse/example-multi-impulse-python — Flask app running multiple impulses (object detection and visual anomaly detection)
- https://github.com/edgeimpulse/example-active-learning-linux-python-sdk — active-learning workflow with the Linux Python SDK
