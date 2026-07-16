---
name: build-arduino-router-rpc
description: Interact with the arduino-router daemon on Arduino UNO Q using MessagePack RPC. Use when creating custom C++, Python, or other clients for Linux MPU to STM32 MCU communication without the Arduino App Lab Python Bridge API.
metadata:
  version: "0.1.0"
---

# Arduino Router RPC

## Core Knowledge

### 1. Architecture Overview
The `arduino-router` is a background `systemd` service on the Linux MPU that acts as a central traffic controller using a **star topology**.
- **Unix Socket**: All clients connect via `/var/run/arduino-router.sock`.
- **Role**: Manages RPC communication between multiple Linux processes and the MCU.
- **Capabilities**:
    - Allows multiple Linux processes to communicate with the MCU simultaneously.
    - Enables Linux-to-Linux communication.
    - Handles service discovery and registration of functions.

### 2. MessagePack RPC Protocol
The protocol uses **MessagePack** (binary format) for efficiency.

#### **Message Types**
| Type | Name | Format | Description |
| :--- | :--- | :--- | :--- |
| **0** | **REQUEST** | `[0, msgid, "method_name", [args]]` | Request a response (e.g., reading a sensor). |
| **1** | **RESPONSE** | `[1, msgid, error, result]` | Response containing return value or error. |
| **2** | **NOTIFY** | `[2, "method_name", [args]]` | Fire-and-forget command (e.g., setting an LED). |

#### **Router Control Methods**
- **Register Function**: `[0, msgid, "$/register", ["method_name"]]`
- **Unregister All**: `[0, msgid, "$/reset", []]`

### 3. Service Management
The router runs as a `systemd` service.

#### **Commands**
- **Status**: `systemctl status arduino-router`
- **Restart**: `sudo systemctl restart arduino-router`
- **Logs**: `journalctl -u arduino-router -f`
- **Enable Verbose Logging**:
  1. `sudo systemctl edit arduino-router.service`
  2. Add `--verbose` to `ExecStart`.
  3. `sudo systemctl daemon-reload && sudo systemctl restart arduino-router`

### 4. Implementation Examples

#### **C++ Implementation**
**Requirements**: `libmsgpack-cxx-dev`
**Key Pattern**: Use `msgpack::pack` to encode and `msgpack::unpacker` to decode. Use a background thread to handle the `receive_loop` and `handle_response` logic.

**Example (Blink):**
- **C++ Client**: Uses `bridge.notify("set_led_state", state)` to send a type 2 message.
- **MCU Sketch**: Uses `Bridge.provide("set_led_base", set_led_state)` to register the function.

#### **Python Implementation**
**Requirements**: `pip3 install msgpack`
**Key Pattern**: Use `socket.AF_UNIX` with `socket.SOCK_STREAM` to connect to the socket. Use `msgpack.Unpacker().feed(data)` to handle incoming byte streams.

**Example (Sensor Read):**
- **Python Client**: `value = bridge.call("read_sensor")` (Type 0).
- **MCU Sketch**: `Bridge.provide("read_sensor", read_sensor)` where the function returns an `int`.

### 5. Troubleshooting
- **Connection Refused**: Check if service is running: `systemctl status arduino-router`.
- **Timeout/Method Not Found**:
    - Ensure MCU side called `Bridge.begin()` and `Bridge.provide()`.
    - Ensure the function name string matches exactly (case-sensitive).
    - Check logs: `journalctl -u arduino-router -n 50`.
- **Debugging Traffic**: Use `socat` to intercept traffic between your app and the router:
  `sudo apt install socat`
  `socat -v UNIX-LISTEN:/tmp/debug.sock,fork UNIX-CONNECT:/var/run/arduino-router.sock`
  (Then point your application to `/tmp/debug.sock`).
