# Contributing to Edge Impulse Agent Skills

Follow the [Agent Skills specification](https://agentskills.io/specification) for skill structure, `SKILL.md` frontmatter, supporting resources, and progressive disclosure. This document only describes conventions specific to this repository.

## Repository conventions

1. Put stable skills in `skills/<skill-name>/`, experimental skills in `skills/.experimental/<skill-name>/`, and deprecated skills in `skills/.deprecated/<skill-name>/`.
2. Use the `edge-impulse-` prefix for Edge Impulse workflows and `arduino-` for Arduino infrastructure. Spell product names as kebab-case components, such as `uno-q`, `app-lab`, and `raspberry-pi`; add `-cpp` or `-python` when the language distinguishes the workflow.
3. Add or update the skill's entry in the catalog table in `README.md`.
4. Do not import third-party content without redistribution permission. Record distinct license terms in the skill as described by the Agent Skills specification.

## Validate changes

Use `skills-ref`, the reference validator from the official [`agentskills/agentskills`](https://github.com/agentskills/agentskills/tree/main/skills-ref) repository. It is a CLI, not an Agent Skill, and is not included here.

Install it outside this repository with [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/agentskills/agentskills.git
cd agentskills/skills-ref
uv sync
source .venv/bin/activate
```

Or use a Python virtual environment:

```bash
git clone https://github.com/agentskills/agentskills.git
cd agentskills/skills-ref
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

From this repository's root, validate each changed skill:

```bash
skills-ref validate skills/<skill-name>
git diff --check
```

In the pull request, describe the source, intended use, overlap analysis, and validation performed.
