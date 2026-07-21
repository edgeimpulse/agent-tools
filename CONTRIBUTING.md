# Contributing to Edge Impulse Agent Skills

Follow the [Agent Skills specification](https://agentskills.io/specification) for skill structure, `SKILL.md` frontmatter, supporting resources, and progressive disclosure. This document only describes conventions specific to this repository.

## Repository conventions

1. Put stable skills in `skills/<skill-name>/`, experimental skills in `skills/.experimental/<skill-name>/`, and deprecated skills in `skills/.deprecated/<skill-name>/`.
2. Use action-oriented prefixes: `firmware-` for skills that integrate exported Edge Impulse models into device or application code and `build-` for build and integration workflows; use the exact name `api` for Edge Impulse platform integrations. Follow the prefix with the relevant platform, tool, or language, such as `build-arduino-` or `firmware-stm32`. Spell product names as kebab-case components, such as `uno-q`, `app-lab`, and `raspberry-pi`; add `-cpp` or `-python` when the language distinguishes the workflow.
3. Add or update the skill's entry in the catalog table in `README.md`.
4. Do not import third-party content without redistribution permission. Record distinct license terms in the skill as described by the Agent Skills specification.
5. When a skill links reference repositories (example projects, official firmware, SDK sources), link repositories from the official [edgeimpulse GitHub organization](https://github.com/edgeimpulse). Confirm each repository is public and not archived before linking — private repositories return 404 for catalog users. Link a third-party repository only when it is the canonical upstream for the platform (for example, Arduino or Zephyr documentation). Add the links as a `## Reference repositories` section in `SKILL.md` — or to the resources list in `references/REFERENCE.md` when the skill has one — with a one-line note on when to consult each repository. Likewise link the relevant [docs.edgeimpulse.com](https://docs.edgeimpulse.com) pages in a `## Documentation` section, and confirm every URL resolves before submitting.

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

Do not manually bump `metadata.version` for ordinary edits. After changes land on `main`, `.github/workflows/bump-skill-versions.yml` increments the patch version of each affected skill and opens a pull request with the result.

In the pull request, describe the source, intended use, overlap analysis, and validation performed.

Every pull request runs `.github/workflows/validate-skills.yml`, which validates all stable and experimental skills with a pinned version of the official reference validator and checks the pull request diff for whitespace errors.
