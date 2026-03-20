# Edge Impulse Agent Skills

This repository contains the public catalog of Edge Impulse Agent Skills.

Agent Skills are reusable building blocks that help agents interact with Edge Impulse data, projects, deployments, and workflows.

This repository is intended for developers and users who want to discover, install, and use skills.

## Installing and removing skills

The recommended way to install and manage skills is via the [skills](https://www.npmjs.com/package/skills) npm package developed by [Vercel](https://github.com/vercel-labs).

Below are some of the common commands for the `skills` CLI tool.

**List all available skills:**

```
npx skills add edgeimpulse/agent-skills --list
```

**Install a skill (interactively):**

```
npx skills add edgeimpulse/agent-skills
```

**Install a specific skill:**

```
npx skills add edgeimpulse/agent-skills --skill <skill-name>
```

**Remove a specific skill:**

```
npx skills remove <skill-name>
```

## Experimental, stable, and deprecated skills

Skills in this repository follow a simple stability model:

- Experimental skills live under `skills/.experimental/`
    - May change or be removed
    - Versions are typically < 1.0.0 (new major versions will start in experimental)
    - Suitable for early adopters and feedback
- Stable skills live under `skills/`
    - Backwards-compatibility is expected in same major version
    - Versions are >= 1.0.0
- When a new major version is released, the previous major version moves to the `skills/.deprecated/` directory

Check each skill’s `SKILL.md` for version and status information.

## Versioning

Skills use semantic versioning (`MAJOR.MINOR.PATCH`):

- `0.x.y` — experimental, breaking changes allowed
- `1.0.0` — first stable release
- `MAJOR` — breaking changes
- `MINOR` — new behavior, backwards-compatible
- `PATCH` — bug fixes only

## Contributing

To report a bug:

- File an issue in this repository

If you would like to propose a new skill or improvements to an existing one:

- Open a pull request against this repository
- Follow the guidelines in [CONTRIBUTING.md](/CONTRIBUTING.md)
