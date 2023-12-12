#!/bin/bash

# Function to handle errors
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Check if pyproject.toml exists
PYPROJECT_FILE="pyproject.toml"
if [ ! -f "$PYPROJECT_FILE" ]; then
    error_exit "$PYPROJECT_FILE does not exist."
fi

# Step 1: Get version from pyproject.toml
VERSION=$(awk -F'=' '/^version/ {gsub(/[" ]/, "", $2); print $2}' "$PYPROJECT_FILE")
if [ -z "$VERSION" ]; then
    error_exit "Unable to extract version from $PYPROJECT_FILE"
fi
echo "Version is $VERSION"

# Step 2: Get package name from pyproject.toml
PACKAGE_NAME=$(awk -F'=' '/^name/ {gsub(/[" ]/, "", $2); print $2}' "$PYPROJECT_FILE")
if [ -z "$PACKAGE_NAME" ]; then
    error_exit "Unable to extract package name from $PYPROJECT_FILE"
fi
echo "PACKAGE_NAME is $PACKAGE_NAME"

# Step 3: Get latest release version from PyPI
PUBLISHED_VERSIONS=$(curl -s "https://pypi.org/pypi/$PACKAGE_NAME/json" | jq -r '.releases | keys | .[]')

if [ -z "$PUBLISHED_VERSIONS" ]; then
    error_exit "Unable to retrieve published version from PyPI for $PACKAGE_NAME"
fi
echo "Published PyPI versions are $PUBLISHED_VERSIONS"

# Step 4: Check if current version is in the list of published versions
PUBLISHING="true"
for ver in $PUBLISHED_VERSIONS; do
    if [ "$ver" == "$VERSION" ]; then
        PUBLISHING="false"
        break
    fi
done
echo "PUBLISHING is $PUBLISHING"
echo "PUBLISHING=$PUBLISHING" >> $GITHUB_ENV
