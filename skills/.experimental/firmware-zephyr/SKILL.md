---
name: firmware-zephyr
description: Integrate Edge Impulse Zephyr Module deployments into Zephyr or Nordic nRF Connect SDK applications, including west manifests, CMake, Kconfig, devicetree sensors, static-buffer inference, clean builds, flashing, and porting across boards. Use for nRF5340 and other Zephyr-supported targets.
metadata:
  version: "0.1.1"
---

# Edge Impulse Zephyr integration

Prefer the Edge Impulse Zephyr Module and a **Zephyr Module** deployment over manually copying a generic C++ export.

## Inspect first

1. Identify the Zephyr or NCS version, exact board qualifier, application/manifest repository, sensor, model type, and current module layout.
2. Inspect `west.yml`, `CMakeLists.txt`, `prj.conf`, overlays, and existing application sources.
3. Confirm compatible revisions from current Edge Impulse and Zephyr/NCS documentation. Do not assume the latest Zephyr module works with every NCS release.

## Add the module and model

For a new reference workspace:

```bash
west init -m https://github.com/edgeimpulse/example-standalone-inferencing-zephyr-module
west update
```

For an existing manifest, add the `edge-impulse-sdk-zephyr` project at a compatible pinned revision and register its west commands when using `west ei-build` or `west ei-deploy`. Then run `west update`.

Export the model as **Zephyr Module**, extract it under `model/`, and verify it contains `CMakeLists.txt`, `edge-impulse-sdk/`, `model-parameters/`, and `tflite-model/`. Make the model discoverable:

```cmake
list(APPEND ZEPHYR_EXTRA_MODULES ${CMAKE_CURRENT_SOURCE_DIR}/model)
```

Place this before `find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})` when required by the project's CMake structure.

## Configure

- Enable C++ and the sensor, bus, logging, and memory options required by the application.
- Configure hardware in devicetree/overlays; do not hardcode controller instances that the board DTS already exposes.
- Use `DEVICE_DT_GET` and Zephyr sensor APIs, and verify `device_is_ready()`.
- Increase `CONFIG_MAIN_STACK_SIZE`, heap, or thread stack only from measured need.
- Preserve NCS sysbuild, child-image, and board qualifier conventions in existing Nordic projects.

## Inference pattern

1. Initialize the sensor and model.
2. Sample at `EI_CLASSIFIER_INTERVAL_MS` or the generated frequency.
3. Store values in training channel order and units.
4. Fill exactly `EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE` values.
5. Construct `signal_t` with a bounds-safe callback.
6. Call `run_classifier()` from thread context.
7. Handle classification, detection, and anomaly outputs according to generated macros.

Use a Zephyr timer, sensor trigger, or dedicated sampling thread plus a ring buffer for continuous inference. Do not run the classifier or blocking logging in an ISR.

## Build and deploy

```bash
west build --pristine -b <board-qualifier>
west flash
```

Always use a pristine build after replacing the model or changing module revisions. Use the board's supported runner when `west flash` needs one.

## nRF5340 specifics

- Select the correct application-core board qualifier for the installed NCS version.
- Keep inference on the application core unless the project architecture explicitly assigns it elsewhere.
- Check TrustZone/nonsecure target conventions, network-core images, partition manager output, and flash/RAM placement before changing linker behavior.
- Use nRF Connect SDK's pinned Zephyr and module compatibility rather than mixing arbitrary upstream revisions.

## Verify

1. Test one raw feature window copied from Studio and compare results.
2. Test live input for sample rate, units, axis/channel order, and ring-buffer overruns.
3. Inspect build RAM/flash reports and thread stack usage.
4. Monitor serial logs after flashing and confirm repeated inference without faults.

## Common failures

- `west: unknown command ei-build`: run inside the manifest workspace, enable extensions, and verify `west-commands` in the manifest.
- Model headers missing: confirm the archive was extracted into `model/` and registered as a module.
- Sensor not ready: inspect devicetree status, aliases, bus pins, and Kconfig driver symbols.
- Inaccurate predictions: compare a known Studio window before changing the model.

## Documentation

- https://docs.edgeimpulse.com/hardware/deployments/run-zephyr-module — Zephyr Module deployment
- https://docs.edgeimpulse.com/hardware/deployments/run-cpp-zephyr-nordic — run the C++ library on Zephyr-based Nordic boards

## Reference repositories

- https://github.com/edgeimpulse/edge-impulse-sdk-zephyr — the Edge Impulse Zephyr module pulled in via west
- https://github.com/edgeimpulse/example-standalone-inferencing-zephyr — older standalone example that vendors the SDK directly instead of using the module

Official Nordic firmware (complete ingestion and inferencing applications built on Zephyr/NCS):

- https://github.com/edgeimpulse/firmware-nordic-nrf52840dk-nrf5340dk
- https://github.com/edgeimpulse/firmware-nordic-thingy53
- https://github.com/edgeimpulse/firmware-nordic-thingy91
- https://github.com/edgeimpulse/firmware-nordic-nrf9160dk
- https://github.com/edgeimpulse/firmware-nordic-nrf91x1
- https://github.com/edgeimpulse/firmware-nordic-nrf7002dk
- https://github.com/edgeimpulse/firmware-nordic-nrf54l15dk
- https://github.com/edgeimpulse/firmware-nordic-nrf54lm20-dk

Focused examples:

- https://github.com/edgeimpulse/ei-zephyr-imu-inference — IMU model on devicetree sensor data
- https://github.com/edgeimpulse/ei-zephyr-mic-kws-inference — keyword spotting on microphone data
- https://github.com/edgeimpulse/ei-zephyr-thread-inference — threads and message queue for continuous inference
- https://github.com/edgeimpulse/ei-zephyr-sensors-dataforwarder — stream sensor data over USB CDC to the Edge Impulse data forwarder
- https://github.com/edgeimpulse/ei-zephyr-ble-gatt-client — BLE GATT client integration
