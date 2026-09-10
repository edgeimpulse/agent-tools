# Edge Impulse Agent Skills

This repository contains the public catalog of Edge Impulse Agent Skills.

Agent Skills are reusable building blocks that help agents interact with Edge Impulse data, projects, deployments, and workflows.

This repository is intended for developers and users who want to discover, install, and use skills. Every skill follows the [Agent Skills specification](https://agentskills.io/specification).

All skill names are prefixed with `ei-` so they stay identifiable once installed alongside skills from other catalogs.

## Stable skills

| Skill | Purpose |
| --- | --- |
| `ei-api` | Edge Impulse APIs, CLIs, & SDKs |
| `ei-build-arduino-uno-q-app-lab` | Arduino UNO Q and App Lab apps, bricks, Edge Impulse model integration, and Flask UIs |
| `ei-firmware-arduino` | Arduino sketches, Edge Impulse library integration |
| `ei-build-custom-deployment-blocks` | Edge Impulse custom deployment blocks |

## Experimental skills

| Skill | Purpose |
| --- | --- |
| `ei-build-arduino-router-rpc` | Custom MessagePack RPC clients for the Arduino UNO Q MPU/MCU router |
| `ei-build-custom-learning-blocks` | Edge Impulse custom learning blocks (custom ML training containers) |
| `ei-firmware-cpp` | Desktop, Linux, and generic MCU C++ apps using exported Edge Impulse libraries |
| `ei-firmware-raspberry-pi-python` | Raspberry Pi and Linux Python inference using EIM models |
| `ei-firmware-stm32` | STM32CubeIDE and FreeRTOS C++ inference integration |
| `ei-firmware-zephyr` | Zephyr and nRF Connect SDK module integration |

## Installing and removing skills

The recommended way to install and manage skills is the [`skills`](https://www.npmjs.com/package/skills) CLI developed by [Vercel](https://github.com/vercel-labs/skills). It needs [Node.js](https://nodejs.org) and Git, and it installs skills for [many coding agents](https://github.com/vercel-labs/skills#supported-agents), including Claude Code, Codex, Cursor, and OpenCode.

### Install

```bash
# See what's available without installing anything
npx skills add edgeimpulse/agent-tools --list

# Pick skills and agents interactively
npx skills add edgeimpulse/agent-tools

# Install specific skills by name
npx skills add edgeimpulse/agent-tools --skill ei-api --skill ei-firmware-arduino

# Install the whole catalog to every detected agent, no prompts
npx skills add edgeimpulse/agent-tools --all

# Install the whole catalog, but choose the agents yourself
npx skills add edgeimpulse/agent-tools --skill '*' --agent claude-code --yes
```

Experimental skills appear alongside stable ones in all of these. Use `--agent` to target specific agents and `--yes` to skip the prompts in CI.

### Choose an installation scope

Everything installs into the current project unless you pass `-g`:

| Scope | Flag | Installed to |
| --- | --- | --- |
| Project (default) | none | `./<agent>/skills/` in the current directory |
| Global | `-g`, `--global` | `~/<agent>/skills/` in your home directory |

```bash
npx skills add edgeimpulse/agent-tools --skill ei-api --global --agent claude-code --yes
```

### List, update, and remove

```bash
# Show the skills you have installed
npx skills list

# Update installed skills to the latest version in this repository
npx skills update ei-api

# Remove a skill (add --global if you installed it globally)
npx skills remove ei-api
```

Run `npx skills remove` with no arguments to pick from the installed skills interactively.

### Upgrading from unprefixed names

Skills in this catalog were previously published without the `ei-` prefix (`api`, `firmware-arduino`, and so on). `npx skills update` does not rename an installed skill, so remove the old copy and install the prefixed one:

```bash
npx skills remove api
npx skills add edgeimpulse/agent-tools --skill ei-api
```

### Try a skill without installing it

```bash
npx skills use edgeimpulse/agent-tools@ei-api --agent claude-code
```

## Catalog lifecycle

The lifecycle directories are repository conventions rather than Agent Skills frontmatter fields:

- Stable skills live under `skills/`
  - Backwards compatibility is expected.
- Experimental skills live under `skills/.experimental/`
  - They may change or be removed.
  - They are suitable for early adopters and feedback.
- Deprecated skills live under `skills/.deprecated/`.

## Skill versions

Each `SKILL.md` stores a semantic version in `metadata.version`. Stable skills start at `1.0.0`; experimental skills start at `0.1.0`.

After a push to `main`, the version workflow increments the patch component once for every skill with changed files and opens a pull request containing those bumps. Changes outside a skill directory do not affect skill versions. Merging a generated version-bump pull request does not trigger another bump.

## Contributing

To report a bug:

- File an issue in this repository

If you would like to propose a new skill or improvements to an existing one:

- Open a pull request against this repository
- Follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).
