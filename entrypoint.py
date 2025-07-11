#!/usr/bin/env python3
"""Check whether the version in pyproject.toml is already on each package index.

Writes one env-var per index:

    CURRENT_VERSION_EXISTS_ON_pypi_org=true|false|unknown-network-error
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request

try:
    import tomllib            # Python ≥3.11
except ModuleNotFoundError:
    import tomli as tomllib   # type: ignore

# Robust PEP-440 comparison (handles rc, a1, post, dev, etc.)
try:
    from packaging.version import parse as vparse # type: ignore
except ModuleNotFoundError:        # extremely rare on GitHub runners
    from distutils.version import LooseVersion as vparse  # type: ignore

GITHUB_ENV = os.getenv("GITHUB_ENV")                 # path injected by Actions runtime


# ────────────────────────────────────────────────────────────────────────────────
def parse_args() -> tuple[str, list[str]]:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__)
    )
    p.add_argument("pyproject", nargs="?", default="pyproject.toml")
    p.add_argument("indexes", nargs="*", help="Host names, e.g. pypi.org test.pypi.org")
    ns = p.parse_args()
    return ns.pyproject, ns.indexes


def read_name_version(pyproject_path: str) -> tuple[str, str]:
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        sys.exit(f"Error: File not found: {pyproject_path}")
    except tomllib.TOMLDecodeError as e:
        sys.exit(f"Error: Failed to parse TOML in {pyproject_path}: {e}")

    if "project" not in data:
        sys.exit(f"Error: {pyproject_path} is missing `[project]` section")

    proj = data["project"]
    for key in ("name", "version"):
        if key not in proj:
            sys.exit(f"Error: {pyproject_path} is missing `[project].{key}`")

    return proj["name"], proj["version"]


def query_index(index: str, package: str) -> list[str] | None:
    """Return list of versions or None on network / JSON errors."""
    url = f"https://{index}/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.load(resp)
        return list(payload["releases"].keys())
    except urllib.error.HTTPError as e:
        if e.code == 404:          # package never uploaded
            return []
        print(f"⚠  {index}: HTTP {e.code} – treated as unavailable", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠  {index}: {e} – treated as unavailable", file=sys.stderr)
        return None


def write_env_line(key: str, value: str):
    """Emit KEY=value to stdout and $GITHUB_ENV (if allowed)."""
    line = f"{key}={value}"
    print(line)
    if GITHUB_ENV:
        with open(GITHUB_ENV, "a", encoding="utf-8") as f:
            f.write(line + "\n")


# ────────────────────────────────────────────────────────────────────────────────
def main() -> None:
    pyproject_path, indexes = parse_args()
    if not os.path.exists(pyproject_path):
        sys.exit(f"Error: {pyproject_path} does not exist.")
    if not indexes:
        sys.exit("Error: at least one index must be specified.")

    name, local_version = read_name_version(pyproject_path)
    print(f"Package: {name}   Version: {local_version}")
    print(f"Indexes to check: {' '.join(indexes)}")

    for idx in indexes:
        key         = idx.replace(".", "_")                # env-safe
        env_var     = f"CURRENT_VERSION_EXISTS_ON_{key}"   # final var name
        versions    = query_index(idx, name)

        if versions is None:
            write_env_line(env_var, "unknown-network-error")
            continue

        if not versions:
            print(f"Versions on {idx}: <none>")
            write_env_line(env_var, "false")
            continue

        if len(versions) > 10:
            latest = max(versions, key=vparse)
            print(f"{idx}: {len(versions)} versions (latest {latest})")
        else:
            print(f"Versions on {idx}: {', '.join(versions)}")

        exists = str(local_version in versions).lower()   # "true" / "false"
        write_env_line(env_var, exists)


if __name__ == "__main__":
    main()
