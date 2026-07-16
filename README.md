# Edge Impulse Agent Skills

This repository contains the public catalog of Edge Impulse Agent Skills.

Agent Skills are reusable building blocks that help agents interact with Edge Impulse data, projects, deployments, and workflows.

This repository is intended for developers and users who want to discover, install, and use skills. Every skill follows the [Agent Skills specification](https://agentskills.io/specification).

## Stable skills

| Skill | Purpose |
| --- | --- |
| `api` | Edge Impulse APIs, CLIs, SDKs, devices, deployments, and custom blocks |
| `build-arduino-uno-q-app-lab` | Arduino UNO Q and App Lab apps, bricks, Edge Impulse models, and Flask UIs |
| `deploy-arduino` | Arduino sketches using exported Edge Impulse libraries |
| `deploy-custom-deployment-blocks` | Edge Impulse custom deployment blocks |

## Experimental skills

| Skill | Purpose |
| --- | --- |
| `build-arduino-router-rpc` | Custom MessagePack RPC clients for the Arduino UNO Q MPU/MCU router |
| `deploy-linux-cpp` | Linux C++ apps using exported Edge Impulse libraries |
| `deploy-raspberry-pi-python` | Raspberry Pi and Linux Python inference using EIM models |
| `deploy-stm32` | STM32CubeIDE and FreeRTOS C++ inference integration |
| `deploy-zephyr` | Zephyr and nRF Connect SDK module integration |

## Installing and removing skills

The recommended way to install and manage skills is via the [skills](https://www.npmjs.com/package/skills) npm package developed by [Vercel](https://github.com/vercel-labs).

Below are some of the common commands for the `skills` CLI tool.

**List all available skills:**

```
npx skills add edgeimpulse/agent-tools --list
```

**Install a skill (interactively):**

```
npx skills add edgeimpulse/agent-tools
```

**Install a specific skill:**

```
npx skills add edgeimpulse/agent-tools --skill <skill-name>
```

**Remove a specific skill:**

```
npx skills remove <skill-name>
```

## Catalog lifecycle

The lifecycle directories are repository conventions rather than Agent Skills frontmatter fields:

- Experimental skills live under `skills/.experimental/`
  - They may change or be removed.
  - They are suitable for early adopters and feedback.
- Stable skills live under `skills/`
  - Backwards compatibility is expected.
- Deprecated skills live under `skills/.deprecated/`.

## Contributing

To report a bug:

- File an issue in this repository

If you would like to propose a new skill or improvements to an existing one:

- Open a pull request against this repository
- Follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).
