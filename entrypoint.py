#!/usr/bin/env python3
"""Check whether the version in pyproject.toml is already on each package index.

Usage examples
    python check_package_version.py                  # default: pyproject.toml  pypi.org
    python check_package_version.py src/pyproject.toml pypi.org custom.repo.local
"""

from __future__ import annotations
import argparse, json, os, sys, textwrap, urllib.error, urllib.request

try:
    import tomllib            # Python ≥3.11
except ModuleNotFoundError:    # GitHub still ships 3.12, but keep a fallback
    import tomli as tomllib # type: ignore

GITHUB_ENV = os.getenv("GITHUB_ENV")                 # path injected by Actions runtime

def parse_args() -> tuple[str, list[str]]:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__)
    )
    p.add_argument("pyproject", nargs="?", default="pyproject.toml")
    p.add_argument("indexes",   nargs="*", help="Host names, e.g. pypi.org test.pypi.org")
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
    missing_keys = [key for key in ("name", "version") if key not in proj]
    if missing_keys:
        keys_str = ", ".join(f"`[project].{k}`" for k in missing_keys)
        sys.exit(f"Error: {pyproject_path} is missing {keys_str}")

    return proj["name"], proj["version"]

def query_index(index: str, package: str) -> list[str] | None:
    url = f"https://{index}/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.load(resp)
        return list(payload["releases"].keys())
    except urllib.error.HTTPError as e:
        if e.code == 404:          # package never uploaded
            return []
        print(f"⚠  {index}: HTTP {e.code} – treating as unavailable", file=sys.stderr)
        return None
    except Exception as e:         # network errors, invalid JSON, …
        print(f"⚠  {index}: {e} – treating as unavailable", file=sys.stderr)
        return None

def write_env_line(key: str, value: str|bool):
    line = f"{key}={value}"
    print(line)
    if GITHUB_ENV:
        with open(GITHUB_ENV, "a", encoding="utf-8") as f:
            f.write(line + "\n")

def main():
    pyproject_path, indexes = parse_args()
    if not os.path.exists(pyproject_path):
        sys.exit(f"Error: {pyproject_path} does not exist.")
    if not indexes:
        sys.exit("Error: at least one index must be specified.")

    name, local_version = read_name_version(pyproject_path)
    print(f"Package: {name}   Version: {local_version}")
    print(f"Indexes to check: {' '.join(indexes)}")

    for idx in indexes:
        key = idx.replace(".", "_")          # env-safe
        index_versions = query_index(idx, name)

        if index_versions is None:
            # Treat as "needs publishing" but don't change global flag
            write_env_line(f"PUBLISHING_{key}", "true")
            continue

        if len(index_versions) > 10:
            latest = max(index_versions, key=lambda v: [int(x) if x.isdigit() else x for x in v.split('.')])
            print(f"{idx}: {len(index_versions)} versions (latest {latest})")
        else:
            print(f"Versions on {idx}: {', '.join(index_versions) if index_versions else '<none>'}")

        write_env_line(f"PUBLISHING_{key}", str(local_version not in index_versions).lower())

if __name__ == "__main__":
    main()
