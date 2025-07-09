#!/usr/bin/env python3
"""Check whether the version in pyproject.toml is already on each package index.

Usage examples
    python check_package_version.py                  # default: pyproject.toml, pypi.org & test.pypi.org
    python check_package_version.py src/pyproject.toml pypi.org custom.repo.local
"""

from __future__ import annotations
import argparse, json, os, sys, textwrap, urllib.error, urllib.request

try:
    import tomllib            # Python ≥3.11
except ModuleNotFoundError:    # GitHub still ships 3.12, but keep a fallback
    import tomli as tomllib

DEFAULT_INDEXES = ["pypi.org"]
GITHUB_ENV = os.getenv("GITHUB_ENV")                 # path injected by Actions runtime

def parse_args() -> tuple[str, list[str]]:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__)
    )
    p.add_argument("pyproject", nargs="?", default="pyproject.toml")
    p.add_argument("indexes",   nargs="*", help="Host names, e.g. pypi.org test.pypi.org")
    ns = p.parse_args()
    return ns.pyproject, (ns.indexes or DEFAULT_INDEXES)

def read_name_version(pyproject_path: str) -> tuple[str,str]:
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    try:
        proj = data["project"]
        return proj["name"], proj["version"]
    except KeyError as e:
        sys.exit(f"Error: {pyproject_path} is missing `[project].{e.args[0]}`")

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

    name, version = read_name_version(pyproject_path)
    print(f"Package: {name}   Version: {version}")
    print(f"Indexes to check: {' '.join(indexes)}")

    needs_publish_globally = True
    for idx in indexes:
        key = idx.replace(".", "_")          # env-safe
        versions = query_index(idx, name)

        if versions is None:
            # Treat as "needs publishing" but don't change global flag
            write_env_line(f"PUBLISHING_{key}", "true")
            continue

        if len(versions) > 10:
            latest = max(versions, key=lambda v: [int(x) if x.isdigit() else x for x in v.split('.')])
            print(f"{idx}: {len(versions)} versions (latest {latest})")
        else:
            print(f"Versions on {idx}: {', '.join(versions) if versions else '<none>'}")

        needs_publish = version not in versions
        if not needs_publish:
            needs_publish_globally = False

        write_env_line(f"PUBLISHING_{key}", str(needs_publish).lower())

    write_env_line("PACKAGE_NAME",    name)
    write_env_line("PACKAGE_VERSION", version)
    write_env_line("PUBLISHING",      str(needs_publish_globally).lower())

if __name__ == "__main__":
    main()
