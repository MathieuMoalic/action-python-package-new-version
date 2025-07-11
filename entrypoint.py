#!/usr/bin/env python3
"""
Parses pyproject.toml, queries the package index,
and sets outputs for GitHub Actions.
"""

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
import tomllib 


def parse_args() -> tuple[str, list[str]]:
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__)
    )
    p.add_argument("pyproject", help="Path to pyproject.toml")
    p.add_argument("index", help="Host name of the package index (e.g., pypi.org)")
    ns = p.parse_args()
    return ns.pyproject, ns.index


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
    """Return list of versions; None on network / JSON errors."""
    url = f"https://{index}/pypi/{package}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.load(resp)
        return list(payload["releases"].keys())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        print(f"⚠  {index}: HTTP {e.code} - treated as unavailable", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠  {index}: {e} - treated as unavailable", file=sys.stderr)
        return None


def set_github_output(name: str, value: str) -> None:
    """Write output to GitHub Actions output file."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        print("⚠ GITHUB_OUTPUT not set; skipping output export.", file=sys.stderr)
        return

    with open(output_path, "a", encoding="utf-8") as f:
        f.write(f"{name}={value}\n")


def main() -> None:
    pyproject_path, index = parse_args()
    if not os.path.exists(pyproject_path):
        sys.exit(f"Error: {pyproject_path} does not exist.")
    if not index:
        sys.exit("Error: index must be specified.")

    name, local_version = read_name_version(pyproject_path)
    print(f"Package: {name}   Version: {local_version}")
    print(f"Index to check: {index}")


    versions = query_index(index, name)
    if versions is None:
        sys.exit(f"Error: Failed to query index {index} for package {name}.")
    if versions:
        print(f"Found versions: {', '.join(versions)}")
    else:
        print(f"No versions found for package {name} on index {index}.")

    set_github_output("package_name", name)
    set_github_output("package_version", local_version)
    set_github_output("current_version_exists", local_version in versions)

if __name__ == "__main__":
    main()
