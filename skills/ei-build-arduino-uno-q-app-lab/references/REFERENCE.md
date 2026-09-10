# Arduino UNO Q & Arduino App Lab Full Reference

## Table of Contents
1. [Arduino UNO Q Hardware](#arduino-uno-q-hardware)
2. [Arduino App Lab Overview](#arduino-app-lab-overview)
3. [App Structure & Configuration](#app-structure--configuration)
4. [Bricks System](#bricks-system)
5. [App Lab CLI Reference](#app-lab-cli-reference)
6. [Bridge: MCU-MPU Communication](#bridge-mcu-mpu-communication)
7. [Deploying Edge Impulse ML Models](#deploying-edge-impulse-ml-models)
8. [Building Flask Web Apps for App Lab](#building-flask-web-apps-for-app-lab)
9. [Converting Existing Projects to App Lab Apps](#converting-existing-projects-to-app-lab-apps)
10. [Camera & Video Handling on UNO Q](#camera--video-handling-on-uno-q)
11. [Storage & Dependency Management](#storage--dependency-management)
12. [Reference Example: Object Detection with Flask](#reference-example-object-detection-with-flask)
13. [Quick Reference Commands](#quick-reference-commands)

---

## Arduino UNO Q Hardware

### Overview
The Arduino UNO Q is a hybrid board combining a powerful MPU and MCU in the classic UNO form factor. It is the first product from the Qualcomm-Arduino partnership.

### Specifications

**Main Processor (MPU) - Qualcomm Dragonwing QRB2210:**
- Quad-core Arm Cortex-A53 at 2.0 GHz
- Adreno 702 GPU (supports ML inference and 3D graphics)
- Dual 13MP Image Signal Processors (ISPs) - supports 2 cameras simultaneously (or single 25MP at 30fps)
- Runs Debian-based Linux
- AI inference on CPU and GPU

**Microcontroller (MCU) - STM32U585:**
- Arm Cortex-M33 up to 160 MHz
- 2 MB flash
- 786 KB SRAM
- Integrated floating-point unit
- Runs Arduino Code on Zephyr RTOS

**SKU Variants:**
| Variant | RAM | eMMC Storage | SKU |
|---------|-----|-------------|-----|
| Standard | 2 GB | 16 GB | ABX00162 |
| Extended | 4 GB | 32 GB | ABX00173 |

**Connectivity:**
- Wi-Fi 5 Dual-band 2.4/5 GHz (integrated antenna)
- Bluetooth 5.1 (onboard antenna)
- WCBN3536A wireless module
- USB-C: power (5V 3A / 7-24 VDC barrel), DisplayPort/HDMI, USB hub

**I/O:**
- 47 digital I/O pins, 6x 14-bit analog inputs, 2x 12-bit DACs, 6x PWM
- 3x USART, 2x UART, 4x I2C, 3x SPI, CAN-FD
- Qwiic connector for Modulino nodes
- Compatible with classic UNO shields
- MIPI-CSI camera and MIPI-DSI display connectors
- Dual RGB LEDs, 8x13 LED matrix

**Dimensions:** 53.34 mm x 68.58 mm

### Usage Modes
1. **Desktop (Tethered)**: USB-connected to PC running Arduino App Lab
2. **Network**: Over local Wi-Fi (requires initial USB setup)
3. **Standalone (SBC)**: Connect monitor + keyboard + mouse via USB-C hub, runs as single-board computer (recommended with 4GB variant)

### Key Filesystem Paths on the Board
```
/home/arduino/                          # User home directory
/home/arduino/ArduinoApps/              # All App Lab applications
/home/arduino/ArduinoApps/<app-name>/   # Individual app directory
/home/arduino/.arduino-bricks/          # Installed bricks
/home/arduino/.arduino-bricks/ei-models/ # Edge Impulse model storage
```

---

## Arduino App Lab Overview

Arduino App Lab is the unified IDE preloaded on the UNO Q. It combines Arduino Sketches, Python scripts, and containerized AI models in one interface.

### Key Features
- Unified development for Linux (Python) and MCU (Arduino C++)
- Pre-loaded AI model bricks: object detection, anomaly detection, image classification, sound recognition, keyword spotting
- Automatic library dependency installation
- Web-based IDE accessible via `http://<device-ip>:7000` or USB
- Docker-based brick containers for AI workloads
- Bridge for MCU-MPU inter-process communication

### Platform Compatibility (for App Lab desktop client)
- Windows 10+ (64-bit)
- macOS 11+ (64-bit)
- Ubuntu 22.04+
- Debian Trixie (64-bit)

### Connection Methods
- **USB**: Direct connection, first-time setup
- **Wi-Fi**: After initial USB setup, access via `http://<boardname>.local:7000`
- **SSH**: `ssh arduino@<boardname>.local` or `ssh arduino@<device-ip>`
- **ADB**: `adb shell` for low-level access

---

## App Structure & Configuration

### App Directory Layout
```
/home/arduino/ArduinoApps/<app-name>/
+-- app.yaml          # App metadata, brick dependencies, ports (read-only in IDE)
+-- main.py           # Primary Python entry point (runs on Linux MPU)
+-- sketch/
|   +-- sketch.ino    # MCU code (runs on STM32, optional)
+-- README.md         # Documentation (optional)
+-- models/           # ML model files (optional, for custom apps)
+-- assets/           # Images, videos, static files (optional)
+-- python/           # Additional Python modules (optional)
```

Apps can be:
- **Python only**: `main.py` runs on the Linux MPU
- **Sketch only**: `sketch.ino` runs on the MCU
- **Both**: Python + Sketch communicating via Bridge

### Sketch Configuration (`sketch/sketch.yaml`)

When including an Arduino sketch, you must create a `sketch.yaml` file to specify the board profile and libraries **with version numbers**:

```yaml
# sketch/sketch.yaml
profiles:
  default:
    platforms:
      - platform: arduino:zephyr
    libraries:
      - Arduino_RouterBridge (0.2.2)
      - ArduinoGraphics (1.1.4)
      - dependency: Arduino_RPClite (0.2.0)
      - dependency: ArxContainer (0.7.0)
      - dependency: ArxTypeTraits (0.3.2)
      - dependency: DebugLog (0.8.4)
      - dependency: MsgPack (0.4.2)
default_profile: default
```

**Key points:**
- Library names MUST include version in parentheses: `LibraryName (x.y.z)`
- Use `dependency:` prefix for transitive dependencies
- No `fqbn` needed - `platform: arduino:zephyr` is sufficient
- `Arduino_LED_Matrix` is bundled with the Zephyr core (no need to list)
- Without version numbers, you'll get "Library not found" errors

### app.yaml Configuration

```yaml
# app.yaml: Main configuration file for an Arduino App Lab application

# User-visible name of the application
name: My Application

# Brief description
description: "What this app does"

# Icon (emoji or short string)
icon: "icon-emoji-here"

# Network ports the application exposes
# IMPORTANT: Use port 5001 for Flask web apps (port 7000 is reserved for App Lab IDE)
ports: [5001]

# Bricks used by this application (empty for standalone Flask apps)
bricks: []

# Example with bricks and Edge Impulse model:
# bricks:
# - arduino:video_object_detection: {}
# - arduino:web_ui: {}
```

### App Execution Model
- Only ONE app can run per board at a time
- `App.run()` must appear at the end of `main.py` when using bricks
- Code after `App.run()` will NOT execute
- Sketch compilation occurs at launch (can take up to a minute)
- For standalone Flask apps (without bricks), just run `python3 main.py`

---

## Bricks System

### What Are Bricks?
Bricks are reusable, modular software components that launch as separate processes alongside apps. They can be Python modules or Docker containers providing specialized functionality.

### Key Characteristics
- Launch in parallel with the app
- Can be AI models (Docker containers), web servers, API connectors
- Multiple bricks can run simultaneously
- Each brick has its own API documentation in the IDE
- Imported as Python modules in `main.py`

**IMPORTANT: Always prefer using a brick when one exists for the task.** Bricks are the standard App Lab pattern and provide tested, containerized functionality. Only fall back to direct SDK usage (e.g., `edge_impulse_linux.image.ImageImpulseRunner`) when no suitable brick is available. If no brick exists for a common capability, consider whether it makes sense to build a new brick — this packages the functionality as a reusable component that other developers can benefit from in the App Lab ecosystem.

### Available Brick Categories
| Category | Description |
|----------|-------------|
| AI - Audio | Sound classification, keyword spotting |
| AI - Computer Vision | Object detection, image classification, anomaly detection |
| AI - Sensor data | Motion detection, sensor analysis |
| API | REST API handlers, external data sources |
| IoT | IoT connectivity and protocols |
| Storage | Data persistence |
| Web User Interface | Web UI hosting via WebSockets at port 7000 |

### Pre-loaded AI Bricks

| Brick | Import | Use Case |
|-------|--------|----------|
| `video_object_detection` | `from arduino.app_bricks.video_objectdetection import VideoObjectDetection` | Detect objects using camera (YoloX Nano default) |
| `ei_keyword_spotting` | `from arduino.app_bricks.keyword_spotting import KeywordSpotting` | Voice command recognition |
| `ei_image_classification` | `from arduino.app_bricks.image_classification import ImageClassification` | Classify images |
| `ei_anomaly_detection` | `from arduino.app_bricks.anomaly_detection import AnomalyDetection` | Visual anomaly detection |
| `ei_sound_classification` | `from arduino.app_bricks.sound_classification import SoundClassification` | Audio classification |
| `motion_detection` | `from arduino.app_bricks.motion_detection import MotionDetection` | Sensor-based motion detection |
| `web_ui` | `from arduino.app_bricks.web_ui import WebUI` | Web UI hosting (port 7000) |

### Using Bricks in Code
```python
# main.py
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection

# Initialize bricks
web = WebUI()
detector = VideoObjectDetection(confidence=0.7)

# Register detection callback
def handle_detections(detections):
    # detections is a dict: {"label": confidence, ...}
    # e.g. {"person": 0.87, "bicycle": 0.66}
    best_label = max(detections, key=detections.get)
    print(f"Detected: {best_label} ({detections[best_label]:.0%})")

detector.on_detect_all(handle_detections)

# MUST be last line - activates all bricks
App.run()
```

### VideoObjectDetection Brick API

| Method | Description |
|--------|-------------|
| `VideoObjectDetection(confidence=0.3, debounce_sec=2.0)` | Constructor. `confidence` sets the detection threshold, `debounce_sec` sets minimum seconds between repeated detections of the same object |
| `on_detect(label, callback)` | Register a callback for a specific object class. Callback takes no arguments |
| `on_detect_all(callback)` | Register a callback for all detections. Callback receives a dict mapping labels to confidence scores |
| `override_threshold(value)` | Change the confidence threshold at runtime |
| `start()` / `stop()` | Control the detection lifecycle |

The brick manages the USB camera and runs inference in a Docker container. When using a custom Edge Impulse model, set `EI_OBJ_DETECTION_MODEL` in `app.yaml` bricks variables.

### Edge Impulse Model Variables
When using AI bricks with custom Edge Impulse models, set these in `app.yaml`:

| Variable | Use Case |
|----------|----------|
| `EI_OBJ_DETECTION_MODEL` | Object detection |
| `EI_CLASSIFICATION_MODEL` | General classification |
| `EI_IMAGE_CLASSIFICATION_MODEL` | Image classification |
| `EI_KEYWORD_SPOTTING_MODEL` | Keyword/voice spotting |
| `EI_AUDIO_CLASSIFICATION_MODEL` | Audio classification |
| `EI_MOTION_DETECTION_MODEL` | Motion/sensor detection |
| `EI_V_ANOMALY_DETECTION_MODEL` | Visual anomaly detection |

### web_ui Brick Details
- Serves HTML/CSS/JS from an `assets` folder
- Communicates with Python via WebSockets
- Available at `http://localhost:7000`
- Use this brick when you want a simple UI tightly integrated with App Lab

---

## App Lab CLI Reference

The `arduino-app-cli` is pre-installed on the Arduino UNO Q for managing apps without the desktop IDE.

### App Management
```bash
# Create a new app
arduino-app-cli app new "my-app"

# Start an app (full path)
arduino-app-cli app start "/home/arduino/ArduinoApps/my-app"

# Start an app (shortcut for user apps)
arduino-app-cli app start user:my-app

# Start an example app
arduino-app-cli app start examples:blink

# Stop a running app
arduino-app-cli app stop "/home/arduino/ArduinoApps/my-app"

# List all apps and their status
arduino-app-cli app list

# View app logs
arduino-app-cli app logs /home/arduino/ArduinoApps/my-app --all
```

### Brick Management
```bash
# List installed bricks
arduino-app-cli brick list

# View brick details
arduino-app-cli brick details arduino:<brick-name>
```

### System Commands
```bash
# Check for system updates
arduino-app-cli system update

# Rename the board
arduino-app-cli system set-name "my-board"

# Enable/disable network access
arduino-app-cli system network enable
arduino-app-cli system network disable

# Clean up unused Docker containers/images (frees storage)
arduino-app-cli system cleanup
```

---

## Bridge: MCU-MPU Communication

The Bridge enables bidirectional communication between the MCU (sketch.ino) and MPU (main.py) using MessagePack RPC over UART (Serial1 at 115200 baud).

### Architecture
- **Router**: Hosted on the MPU as the `Arduino-Router` service
- **Topology**: Star network with the Router as the central hub
- **Protocol**: MessagePack RPC with frame format `[type, id, method, parameters]`

### Arduino Side (MCU) - `Arduino_RouterBridge` Library

```cpp
#include <Arduino_RouterBridge.h>

void setup() {
    Bridge.begin();  // Initialize Bridge communication

    // Expose functions for Python to call
    Bridge.provide("my_function", myHandler);

    // Use provide_safe() for GPIO operations (thread-safe)
    Bridge.provide_safe("set_led", setLedHandler);
}

// Handler function - receives data from Python
void myHandler(String data) {
    Serial.println("Received: " + data);
}

void setLedHandler(bool state) {
    digitalWrite(LED_BUILTIN, state ? HIGH : LOW);
}

void loop() {
    // Call Python function (synchronous, waits for response)
    int result = 0;
    Bridge.call("python_function", 42).result(result);

    // Notify Python (fire-and-forget, no response)
    Bridge.notify("sensor_data", analogRead(A0));

    delay(100);
}
```

### Python Side (MPU)

```python
from arduino.bridge import Bridge

bridge = Bridge()

# Expose function for MCU to call
@bridge.on_call("python_function")
def handle_call(value):
    return value * 2  # Return value sent back to MCU

# Handle notifications from MCU (no response needed)
@bridge.on_notify("sensor_data")
def handle_sensor(value):
    print(f"Sensor: {value}")

# Call MCU function
bridge.call("my_function", "Hello from Python")

# Notify MCU (fire-and-forget)
bridge.notify("set_led", True)

App.run()  # Required when using bricks
```

### Key Methods

| Method | Direction | Description |
|--------|-----------|-------------|
| `provide(name, handler)` | MCU | Expose function for Python to call |
| `provide_safe(name, handler)` | MCU | Thread-safe version for GPIO operations |
| `call(name, args...)` | Both | Synchronous call, waits for response |
| `notify(name, args...)` | Both | Fire-and-forget, no response |

### Best Practices
- Use `provide_safe()` for handlers that use `digitalWrite()`, `analogRead()`, etc.
- Use `notify()` for telemetry/status updates (faster than `call()`)
- Use `call()` when you need a return value
- Check `call().result(var)` return value - returns `false` on failure

---

## LED Matrix Control (8x13 Built-in Display)

The Arduino UNO Q has a built-in 8x13 LED matrix (monochrome) controlled via the `Arduino_LED_Matrix` library.

### Required Libraries
```cpp
#include <ArduinoGraphics.h>      // For text rendering
#include <Arduino_LED_Matrix.h>   // For matrix control
```

### Basic Setup
```cpp
ArduinoLEDMatrix matrix;

void setup() {
    matrix.begin();
}
```

### Core Methods

| Method | Description |
|--------|-------------|
| `matrix.begin()` | Initialize the LED matrix |
| `matrix.beginDraw()` / `matrix.endDraw()` | Frame drawing operations |
| `matrix.clear()` | Clear all pixels |
| `matrix.set(x, y, r, g, b)` | Set pixel (any non-zero = on) |
| `matrix.stroke(color)` | Set drawing color |

### Text Display Methods (with ArduinoGraphics)

| Method | Description |
|--------|-------------|
| `matrix.textFont(Font_4x6)` | Set font (Font_4x6, Font_5x7) |
| `matrix.textScrollSpeed(ms)` | Set scroll speed in milliseconds |
| `matrix.beginText(x, y, color)` | Start text at position |
| `matrix.println(text)` | Print text |
| `matrix.endText(SCROLL_LEFT)` | End text with scroll direction |

### Example: Scrolling Text Display
```cpp
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

ArduinoLEDMatrix matrix;

void displayText(String text) {
    matrix.beginDraw();
    matrix.stroke(0xFFFFFFFF);           // White color
    matrix.textScrollSpeed(80);           // 80ms between scroll steps
    matrix.textFont(Font_4x6);            // Small font fits 8px height
    matrix.beginText(0, 1, 0xFFFFFF);     // Start at (0,1)
    matrix.println(text);
    matrix.endText(SCROLL_LEFT);          // Scroll left
    matrix.endDraw();
}

void setup() {
    matrix.begin();
    displayText("Hello!");
}

void loop() {
    delay(100);
}
```

### Scroll Directions
- `SCROLL_LEFT` - Text scrolls from right to left
- `SCROLL_RIGHT` - Text scrolls from left to right

---

## Complete Example: Python to LED Matrix via Bridge

This example shows how to send OCR results (or any text) from Python to the MCU's LED matrix.

### Arduino Sketch (`sketch/sketch.ino`)
```cpp
#include <Arduino_RouterBridge.h>
#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

ArduinoLEDMatrix matrix;
String currentText = "";
bool newTextAvailable = false;

void displayText(String text) {
    if (text.length() > 0 && text != currentText) {
        currentText = text;
        newTextAvailable = true;
    }
}

void setup() {
    Serial.begin(115200);
    matrix.begin();
    Bridge.begin();
    Bridge.provide("display_text", displayText);

    // Startup message
    matrix.beginDraw();
    matrix.stroke(0xFFFFFFFF);
    matrix.textFont(Font_4x6);
    matrix.beginText(0, 1, 0xFFFFFF);
    matrix.println("Ready");
    matrix.endText(SCROLL_LEFT);
    matrix.endDraw();
}

void loop() {
    if (newTextAvailable) {
        matrix.beginDraw();
        matrix.stroke(0xFFFFFFFF);
        matrix.textScrollSpeed(80);
        matrix.textFont(Font_4x6);
        matrix.beginText(0, 1, 0xFFFFFF);
        matrix.println(currentText);
        matrix.endText(SCROLL_LEFT);
        matrix.endDraw();
        newTextAvailable = false;
    }
    delay(50);
}
```

### Python Code (`main.py` or `web_inference.py`)
```python
# Bridge for MCU communication (Arduino UNO Q only)
_bridge = None
_last_text = ""

try:
    from arduino.bridge import Bridge
    _bridge = Bridge()
except ImportError:
    pass  # Not on UNO Q

def send_to_led_matrix(text: str) -> None:
    """Send text to the MCU's LED matrix display."""
    global _last_text
    if _bridge and text and text != _last_text:
        try:
            _bridge.notify("display_text", text)
            _last_text = text
        except Exception as e:
            print(f"Bridge error: {e}")

# Usage in your inference loop:
# send_to_led_matrix("Recognized text here")
```

---

## Deploying Edge Impulse ML Models

### Step 1: Export from Edge Impulse Studio
1. Train your impulse in Edge Impulse Studio
2. Go to **Deployment**
3. Select the target hardware as **Arduino UNO Q**
4. Export as `.eim` file for:
   - **"Arduino UNO Q"** (CPU inference)
   - **"Linux aarch64"** (CPU inference)
   - **"Linux Arduino UNO Q (GPU)"** (GPU-accelerated inference via Adreno 702)

### Step 2: Transfer Model to Device
```bash
# Deploy the model via Arduino AppLab as defined here. Follow the instructions
https://docs.edgeimpulse.com/hardware/deployments/run-arduino-app-lab#download-and-select-the-new-custom-model

# This is the old way to move the model via SCP.
scp your-model.eim arduino@<device-ip>:/home/arduino/.arduino-bricks/ei-models/
```

### Step 3: Make Model Executable
```bash
# CRITICAL: In case you copied the .eim files must have execute permission
chmod +x /home/arduino/.arduino-bricks/ei-models/*.eim
# Or for app-local models:
chmod +x /home/arduino/ArduinoApps/my-app/models/*.eim
```

### Step 4: Run
```bash
# With App Lab CLI
arduino-app-cli app start user:my-app

# Or directly
cd /home/arduino/ArduinoApps/my-app
python3 main.py
# OR with venv:
source .venv/bin/activate && python3 main.py
```

### Using Edge Impulse SDK Directly (Without Bricks)
For custom Flask apps that bypass the brick system:

```python
from edge_impulse_linux.image import ImageImpulseRunner

runner = ImageImpulseRunner('./models/model.eim')
model_info = runner.init()

# Classify a frame (numpy array, RGB, flattened)
features = frame_rgb.flatten().tolist()
result = runner.classify(features)

# result['result'] contains classification/detection output
runner.stop()
```

---

## Building Flask Web Apps for App Lab

### Architecture Pattern
For custom web UIs (instead of the `web_ui` brick), use Flask on port 5001:

```
app-name/
+-- app.yaml              # ports: [5001], bricks: []
+-- python/
|   +-- main.py            # Flask app entry point
|   +-- requirements.txt   # Python dependencies
|   +-- templates/
|   |   +-- index.html     # Web UI
|   |   +-- assets/        # CSS, JS, images
|   +-- utils/
|       +-- mock_dependencies.py  # Dependency mocks (optional)
+-- models/                # .eim model files
+-- assets/                # Images, videos for inference
```

### app.yaml for Flask Apps
```yaml
name: My Custom Detection App
description: "Real-time detection with Flask web UI"
icon: "icon-emoji-here"
ports: [5001]
bricks: []
```

### Mock Dependencies (Required for edge_impulse_linux)
Create `python/utils/mock_dependencies.py` to avoid pyaudio/six import issues:

```python
import sys
import builtins

def apply_mocks():
    """Apply mocks for six and pyaudio to avoid dependency issues."""
    class MockSixMovesQueue:
        Queue = None

    class MockSixMoves:
        queue = MockSixMovesQueue()

    class MockSix:
        moves = MockSixMoves()

    sys.modules['six'] = MockSix()
    sys.modules['six.moves'] = MockSixMoves()
    sys.modules['six.moves.queue'] = MockSixMovesQueue()

    class MockPyAudio:
        pass

    sys.modules['pyaudio'] = MockPyAudio()
    builtins.pyaudio = MockPyAudio()
```

Call `apply_mocks()` at the top of `main.py` BEFORE importing edge_impulse_linux.

### Requirements.txt for Flask Apps
```
edge-impulse-linux==1.2.2
opencv-python-headless
flask
numpy
requests
```

**IMPORTANT:** Use `opencv-python-headless` (not `opencv-python`) on the UNO Q - the headless variant is smaller and doesn't need GUI libraries.

### Flask App Template
```python
#!/usr/bin/env python3
"""
Flask web application for Edge Impulse inference on Arduino UNO Q.
"""

# Apply mocks BEFORE importing edge_impulse_linux
from utils.mock_dependencies import apply_mocks
apply_mocks()

import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify, request
from edge_impulse_linux.image import ImageImpulseRunner

app = Flask(__name__)

# Initialize model
runner = ImageImpulseRunner('./models/model.eim')
model_info = runner.init()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """MJPEG video stream endpoint."""
    def generate():
        cap = cv2.VideoCapture(2, cv2.CAP_V4L2)  # /dev/video2 for Logitech BRIO RGB
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)
```

---

## Converting Existing Projects to App Lab Apps

When adapting an existing Python project to run as an Arduino App Lab application, follow these steps:

### 1. Create App Structure
```bash
# On the Arduino UNO Q
arduino-app-cli app new "my-app"
# OR manually:
mkdir -p /home/arduino/ArduinoApps/my-app
```

### 2. Create app.yaml
```yaml
name: My Converted App
description: "Adapted from existing project"
icon: "icon-emoji-here"
ports: [5001]      # If the app has a web UI
bricks: []         # Empty for standalone Flask apps
```

### 3. Set Up Python Environment
```bash
cd /home/arduino/ArduinoApps/my-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Adapt the Code
Key changes needed when converting:
- **Port**: Use port 5001 (port 7000 is reserved for App Lab IDE)
- **Host**: Bind to `0.0.0.0` (not `localhost`) so it's accessible over the network
- **Camera**: Use V4L2 backend and correct device index (see Camera section below)
- **Models**: Ensure `.eim` files are `chmod +x` and use `linux-aarch64` architecture
- **OpenCV**: Use `opencv-python-headless` instead of `opencv-python`
- **Dependencies**: Add `mock_dependencies.py` for edge_impulse_linux compatibility
- **Python version**: Python 3.10+ syntax (e.g., `str | None`) is supported on the UNO Q

### 5. Launch with App Lab CLI
```bash
# Start the app
arduino-app-cli app start user:my-app

# Or run directly
cd /home/arduino/ArduinoApps/my-app
source .venv/bin/activate
python3 python/main.py
```

### 6. Access the Web UI
Open `http://<device-ip>:5001` from any browser on the same network.

---

## Camera & Video Handling on UNO Q

### Video Device Mapping
The UNO Q exposes multiple `/dev/video*` devices. Not all are cameras:

| Device | Type | Description |
|--------|------|-------------|
| `/dev/video0` | Encoder | Qualcomm Venus video encoder (NOT a camera) |
| `/dev/video1` | Decoder | Qualcomm Venus video decoder (NOT a camera) |
| `/dev/video2` | RGB Camera | External USB camera main stream (e.g., Logitech BRIO) |
| `/dev/video3` | Metadata | Camera metadata stream |
| `/dev/video4` | IR Camera | Infrared stream (if camera supports it) |
| `/dev/video5` | Metadata | IR metadata stream |

### Camera Detection Best Practices
1. **Always filter out Venus encoder/decoder devices** - they show as video devices but are NOT cameras
2. **Use V4L2 backend** on Linux: `cv2.VideoCapture(index, cv2.CAP_V4L2)`
3. **Check device info** with `v4l2-ctl --device /dev/videoN --info` to identify real cameras
4. **Identify IR cameras** - some cameras (like Logitech BRIO) expose both RGB and IR streams
5. **Use `/dev/video2`** as the typical default for the first USB camera's RGB stream

### Camera Detection Code Pattern
```python
import subprocess
import cv2
import glob

def detect_cameras():
    """Detect real cameras, filtering out encoders/decoders."""
    cameras = []
    for device in sorted(glob.glob('/dev/video*')):
        index = int(device.replace('/dev/video', ''))
        try:
            result = subprocess.run(
                ['v4l2-ctl', '--device', device, '--info'],
                capture_output=True, text=True, timeout=2
            )
            output = result.stdout
            # Extract card name
            card_name = None
            for line in output.split('\n'):
                if 'Card type' in line:
                    card_name = line.split(':', 1)[1].strip()

            # Skip encoder/decoder devices
            if card_name and ('venus' in card_name.lower() or
                            'encoder' in card_name.lower() or
                            'decoder' in card_name.lower()):
                continue

            # Must be a Video Capture device
            if 'Video Capture' not in output:
                continue

            # Try to open and read a frame
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    cameras.append({'index': index, 'name': card_name or f'Camera {index}'})
        except Exception:
            continue
    return cameras
```

### MJPEG Format for Performance
```python
cap = cv2.VideoCapture(2, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```

---

## Storage & Dependency Management

The Arduino UNO Q has limited storage (16GB or 32GB eMMC). The `/home/arduino` partition is typically 3.6GB.

### Freeing Space
```bash
# Check disk usage
df -h

# Find large directories
du -sh /home/arduino/* | sort -rh | head -20

# Clean pip cache
pip cache purge

# Clean apt cache
sudo apt clean && sudo apt autoremove -y

# Clean unused Docker images/containers (big space savings)
docker system prune -a
# Or via CLI:
arduino-app-cli system cleanup

# Clean journal logs
sudo journalctl --vacuum-size=50M
```

### If /home Is Full, Use Root Partition
```bash
# Create venv on root partition (usually has more space)
sudo mkdir -p /opt/app-venv
sudo chown arduino:arduino /opt/app-venv
python3 -m venv /opt/app-venv
source /opt/app-venv/bin/activate
pip install -r requirements.txt
```

### Dependency Tips
- Use `opencv-python-headless` instead of `opencv-python` (much smaller)
- Pin `edge-impulse-linux==1.2.2` for compatibility
- Use `--no-cache-dir` with pip to avoid filling cache: `pip install --no-cache-dir -r requirements.txt`

---

## Reference Example: Object Detection with Flask

Based on the [Edge Impulse Arduino App Lab example](https://github.com/edgeimpulse/example-arduino-app-lab-object-detection-using-flask):

### Project Structure
```
example-app/
+-- app.yaml
+-- models/
|   +-- model-linux-aarch64.eim
+-- assets/
|   +-- sample-image.jpg
+-- python/
|   +-- main.py
|   +-- requirements.txt
|   +-- templates/
|   |   +-- index.html
|   |   +-- assets/
|   +-- utils/
|       +-- mock_dependencies.py
+-- .python-version          # 3.13.5
```

### app.yaml
```yaml
name: Custom object detection with Edge Impulse
description: "Real-time object detection using Edge Impulse models and Flask"
icon: "icon-emoji-here"
ports: [5001]
bricks: []
```

### requirements.txt
```
edge-impulse-linux==1.2.2
opencv-python-headless
flask
numpy
requests
```

### Key Features of the Example
- Multi-source input: camera, RTSP streams, image files, video files
- Real-time inference with MJPEG streaming (`/video_feed`, `/inference_feed`)
- Model switching via web UI
- Frame upload to Edge Impulse Studio with bounding box labels
- Deployment workflow (build, poll status, download model)
- Runs on macOS (arm64) and Linux (aarch64)

### Running on Arduino UNO Q
```bash
# Clone into ArduinoApps
cd /home/arduino/ArduinoApps
git clone https://github.com/edgeimpulse/example-arduino-app-lab-object-detection-using-flask.git my-detection-app
cd my-detection-app

# Make models executable
chmod +x models/*.eim

# Start via CLI
arduino-app-cli app start .

# Or manually with venv
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r python/requirements.txt
python3 python/main.py
```

Access at `http://<device-ip>:5001`

---

## Quick Reference Commands

```bash
# === Connection ===
ssh arduino@<device-ip>
adb shell

# === App Management ===
arduino-app-cli app new "my-app"
arduino-app-cli app start user:my-app
arduino-app-cli app stop user:my-app
arduino-app-cli app list
arduino-app-cli app logs user:my-app --all

# === Model Deployment ===
scp model.eim arduino@<device-ip>:/home/arduino/ArduinoApps/my-app/models/
ssh arduino@<device-ip> "chmod +x /home/arduino/ArduinoApps/my-app/models/*.eim"

# === Brick Management ===
arduino-app-cli brick list
arduino-app-cli brick details arduino:<brick-name>

# === System ===
arduino-app-cli system update
arduino-app-cli system cleanup
df -h
docker system prune -a

# === Camera ===
v4l2-ctl --list-devices
v4l2-ctl --device /dev/video2 --info

# === Python Environment ===
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt

# === Network ===
hostname -I       # Get device IP
```

---

## Additional Resources from Community Knowledge Base

### Additional Bridge Patterns

#### Using `call()` with Return Values (MCU-side handlers)
```cpp
// MCU: Handler that returns a value
String getValueHandler() {
    return String(analogRead(A0));
}

// Python side:
result = bridge.call("getValueHandler")  # Returns the string value
```

#### Async Notifications (Fire-and-Forget)
```cpp
// MCU: Fire notification (no response needed)
Bridge.notify("buttonPressed", digitalRead(BUTTON_PIN));

// Python side: Handle notifications
@bridge.on_notify("buttonPressed")
def handle_button(value):
    print(f"Button state: {value}")
```

#### Multiple Parameters
```python
# Pass multiple parameters as comma-separated string
bridge.call("setPWM", "9,128")  # pin, value

// MCU side: Parse the string
void setPWM(String params) {
    int comma = params.indexOf(',');
    int pin = params.substring(0, comma).toInt();
    int value = params.substring(comma + 1).toInt();
    analogWrite(pin, value);
}
```

---

## Community Troubleshooting Additions

### Common Bridge Communication Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `call()` returns empty | MCU not initialized | Add 2-3 second delay before first call |
| `call()` times out | Function blocks too long | Keep handlers non-blocking, use `delay(10)` in loop |
| Function not found | Name mismatch | Check exact spelling matches between MCU and Python |
| Serial errors | Wrong baud rate | Verify 115200 baud on both sides |

### Non-Blocking Animation Pattern (MCU)
```cpp
enum AnimationState { IDLE, SCROLLING, ANIMATING };
AnimationState state = IDLE;
String displayText = "";
int scrollOffset = 0;

void loop() {
    switch (state) {
        case SCROLLING:
            // Process ONE step per loop iteration
            scrollOffset++;
            if (scrollOffset > displayText.length() * 6) {
                state = IDLE;
            }
            break;
        case ANIMATING:
            // Animation frame processing
            break;
    }
    Bridge.update();  // Critical: keeps RPC responsive
    delay(50);
}
```

### LED Matrix I2C Troubleshooting
```cpp
// I2C Scanner - paste in setup() to find device addresses
Wire.begin();
Serial.println("Scanning I2C devices...");
for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
        Serial.print("Found: 0x");
        Serial.println(addr, HEX);
    }
}
```

### Network Troubleshooting
```bash
# Check Wi-Fi status
nmcli device wifi list

# Get IP address
hostname -I

# Test connectivity
ping google.com

# View network logs
journalctl -u NetworkManager | tail -20
```

### Deployment via ADB (Alternative to SSH)
```bash
# Port forwarding for web UI access
adb forward tcp:7000 tcp:7000

# Push files
adb push local/file /home/arduino/project/

# Shell access
adb shell

# View logs
adb logcat | grep arduino
```

---

## Resources

- [Arduino App Bricks Library (GitHub)](https://github.com/arduino/app-bricks-py)
- [Edge Impulse App Lab Deployment Docs](https://docs.edgeimpulse.com/hardware/deployments/run-arduino-app-lab)
- [Arduino UNO Q Documentation](https://docs.arduino.cc/hardware/uno-q)
- [Example: Object Detection with Flask](https://github.com/edgeimpulse/example-arduino-app-lab-object-detection-using-flask)
- [Example: Accelerometer Data Collection](https://github.com/edgeimpulse/example-arduino-app-lab-accelerometer-data-collection) — collect labeled accelerometer data from a live web UI and upload it to Edge Impulse
- [Example: Rock Paper Scissors](https://github.com/edgeimpulse/example-rock-paper-scissors-Arduino-UNO-Q) — real-time object-detection game on the UNO Q
- [Example: Custom Analog Sensor](https://github.com/edgeimpulse/ei-unoq-custom-sensor) — MCU analog sampling streamed to the Linux MPU for EIM inference in Python
- [Example: Braccio Arm](https://github.com/edgeimpulse/unoq-braccio) — TinkerKit Braccio arm with UNO Q, ROS 2, Edge Impulse, and Gazebo
- [Arduino UNO Q Docs Source](https://github.com/arduino/docs-content/tree/main/content/hardware/02.uno/boards/uno-q)
- [Arduino App Lab Docs Source](https://github.com/arduino/docs-content/tree/main/content/software/app-lab)
- [Community Knowledge Base](https://github.com/CWTI-Ltd/arduino_uno_q_knowledge_base_and_playground)
