#!/usr/bin/env python3
"""Bump versions for skills changed between two Git revisions."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Iterable


SEMVER_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
ZERO_SHA_PATTERN = re.compile(r"^0+$")


def changed_paths(repo: Path, base: str, head: str) -> list[str]:
    """Return added, copied, modified, or renamed paths for a push range."""
    if ZERO_SHA_PATTERN.fullmatch(base):
        command = [
            "git",
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            head,
        ]
    else:
        command = [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            "--find-renames",
            "-z",
            base,
            head,
        ]

    result = subprocess.run(
        command,
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return [path for path in result.stdout.split("\0") if path]


def changed_skill_directories(repo: Path, paths: Iterable[str]) -> list[Path]:
    """Map changed repository paths to their nearest containing skill."""
    skill_dirs: set[Path] = set()

    for raw_path in paths:
        relative = PurePosixPath(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            continue
        if not relative.parts or relative.parts[0] != "skills":
            continue

        candidate = repo.joinpath(*relative.parts).parent
        while candidate != repo and repo in candidate.parents:
            if (candidate / "SKILL.md").is_file():
                skill_dirs.add(candidate)
                break
            candidate = candidate.parent

    return sorted(skill_dirs)


def default_version(skill_dir: Path) -> str:
    """Choose the initial version from the skill lifecycle directory."""
    return "0.1.0" if ".experimental" in skill_dir.parts else "1.0.0"


def _unquote_version(value: str, skill_file: Path) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    if not SEMVER_PATTERN.fullmatch(value):
        raise ValueError(
            f"{skill_file}: metadata.version must be a quoted MAJOR.MINOR.PATCH value"
        )
    return value


def bump_skill_version(skill_dir: Path) -> tuple[str | None, str]:
    """Increment a skill's patch version, initializing missing metadata."""
    skill_file = skill_dir / "SKILL.md"
    lines = skill_file.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{skill_file}: missing opening YAML frontmatter delimiter")

    try:
        frontmatter_end = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise ValueError(f"{skill_file}: missing closing YAML frontmatter delimiter") from error

    metadata_index = next(
        (
            index
            for index in range(1, frontmatter_end)
            if re.fullmatch(r"metadata:\s*", lines[index].rstrip("\r\n"))
        ),
        None,
    )

    if metadata_index is None:
        new_version = default_version(skill_dir)
        lines[frontmatter_end:frontmatter_end] = [
            "metadata:\n",
            f'  version: "{new_version}"\n',
        ]
        previous_version = None
    else:
        metadata_end = frontmatter_end
        for index in range(metadata_index + 1, frontmatter_end):
            content = lines[index].rstrip("\r\n")
            if content and not content[0].isspace() and not content.lstrip().startswith("#"):
                metadata_end = index
                break

        version_index = next(
            (
                index
                for index in range(metadata_index + 1, metadata_end)
                if re.match(r"^[ \t]+version:\s*", lines[index])
            ),
            None,
        )

        if version_index is None:
            new_version = default_version(skill_dir)
            lines[metadata_index + 1 : metadata_index + 1] = [
                f'  version: "{new_version}"\n'
            ]
            previous_version = None
        else:
            match = re.match(r"^[ \t]+version:\s*(.*?)\s*(?:\r?\n)?$", lines[version_index])
            if match is None:
                raise ValueError(f"{skill_file}: could not parse metadata.version")
            previous_version = _unquote_version(match.group(1), skill_file)
            major, minor, patch = (int(part) for part in previous_version.split("."))
            new_version = f"{major}.{minor}.{patch + 1}"
            indentation = lines[version_index][
                : len(lines[version_index]) - len(lines[version_index].lstrip())
            ]
            lines[version_index] = f'{indentation}version: "{new_version}"\n'

    skill_file.write_text("".join(lines), encoding="utf-8")
    return previous_version, new_version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Base Git revision from the push event")
    parser.add_argument("--head", default="HEAD", help="Head Git revision (default: HEAD)")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed paths; when omitted, --base and --head are diffed",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )

    paths = args.paths
    if not paths:
        if not args.base:
            raise SystemExit("--base is required when changed paths are not provided")
        paths = changed_paths(repo, args.base, args.head)

    skill_dirs = changed_skill_directories(repo, paths)
    if not skill_dirs:
        print("No changed skills found.")
        return 0

    for skill_dir in skill_dirs:
        previous, current = bump_skill_version(skill_dir)
        relative = skill_dir.relative_to(repo)
        if previous is None:
            print(f"Initialized {relative} at {current}")
        else:
            print(f"Bumped {relative} from {previous} to {current}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
