#!/usr/bin/env bash
# check-package-version.sh
#
# Usage examples
#   ./check-package-version.sh                 # looks at pyproject.toml, checks pypi + test.pypi
#   ./check-package-version.sh src/pyproject.toml pypi.org custom.repo.local
#
# Requires: curl, jq, awk, bash 4+

set -euo pipefail

########## helper ##########
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

########## inputs ##########
PYPROJECT_FILE="${1:-pyproject.toml}"

# Default indexes to probe.  Feel free to add more.
DEFAULT_INDEXES=(pypi.org test.pypi.org)

# If the caller listed extra indexes on the command line use those, otherwise defaults.
shift || true            # shift once so $@ now holds any extra args
INDEXES=("${@:-${DEFAULT_INDEXES[@]}}")

########## validate file ##########
[[ -f "$PYPROJECT_FILE" ]] || error_exit "$PYPROJECT_FILE does not exist."

########## extract name & version ##########
VERSION=$(awk -F'=' '/^[[:space:]]*version[[:space:]]*=/ \
         {gsub(/["'\'']|[[:space:]]/, "", $2); print $2}' "$PYPROJECT_FILE")
[[ -n "$VERSION" ]] || error_exit "Unable to extract version from $PYPROJECT_FILE"

PACKAGE_NAME=$(awk -F'=' '/^[[:space:]]*name[[:space:]]*=/ \
              {gsub(/["'\'']|[[:space:]]/, "", $2); print $2}' "$PYPROJECT_FILE")
[[ -n "$PACKAGE_NAME" ]] || error_exit "Unable to extract package name from $PYPROJECT_FILE"

echo "Package: $PACKAGE_NAME   Version: $VERSION"
echo "Indexes to check: ${INDEXES[*]}"

########## main loop ##########
NEED_PUBLISH_ALL=true   # stays true only if every individual index says "needs publish"

for INDEX in "${INDEXES[@]}"; do
    # Replace dots with underscores to build an env-safe key, e.g. pypi_org
    INDEX_KEY="${INDEX//./_}"

    # Query the JSON.  Handle 404 (package never uploaded) and network errors gracefully.
    if JSON=$(curl -sSfL "https://${INDEX}/pypi/${PACKAGE_NAME}/json" 2>/dev/null); then
        PUBLISHED_VERSIONS=$(jq -r '.releases | keys | .[]' <<<"$JSON" | tr '\n' ' ')
    else
        echo "⚠️  Could not retrieve metadata from ${INDEX}; assuming version not present there."
        PUBLISHED_VERSIONS=""
    fi

    echo "Versions on ${INDEX}: ${PUBLISHED_VERSIONS:-<none>}"

    PUBLISHING_FOR_INDEX=true
    for ver in $PUBLISHED_VERSIONS; do
        if [[ "$ver" == "$VERSION" ]]; then
            PUBLISHING_FOR_INDEX=false
            NEED_PUBLISH_ALL=false   # because at least one index already has the version
            break
        fi
    done

    echo "PUBLISHING_${INDEX_KEY}=${PUBLISHING_FOR_INDEX}"
    echo "PUBLISHING_${INDEX_KEY}=${PUBLISHING_FOR_INDEX}" >> "${GITHUB_ENV:-/dev/null}"
done

########## aggregate flag ##########
echo "PUBLISHING=${NEED_PUBLISH_ALL}"
echo "PUBLISHING=${NEED_PUBLISH_ALL}" >> "${GITHUB_ENV:-/dev/null}"

########## always useful info ##########
echo "PACKAGE_NAME=$PACKAGE_NAME"    >> "${GITHUB_ENV:-/dev/null}"
echo "PACKAGE_VERSION=$VERSION"      >> "${GITHUB_ENV:-/dev/null}"
