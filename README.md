# Python Package Version Check – GitHub Action

Quickly find out whether the version declared in your `pyproject.toml` is **already published** to one or more Python package indexes (PyPI, Test PyPI, a private index, …).

---

## 📦 What it does

1. Reads **`project.name`** and **`project.version`** from the supplied `pyproject.toml`.
2. Queries each index you specify (defaults to `pypi.org`).
3. Compares the local version against the list of released versions.
4. Exposes result flags via:

   * **environment variables** (for debugging inside the step)

---

## 🛠 Usage

```yaml
name: Build & Publish

on:
  push:
    branches: [ main ]
    tags:     [ 'v[0-9]+.[0-9]+.[0-9]+' ]

jobs:
  check-version:
    runs-on: ubuntu-latest
    outputs:
      exists: ${{ steps.check.outputs.exists }}
      version: ${{ steps.check.outputs.version }}
    steps:
      - uses: actions/checkout@v4

      - name: Check package version on all indexes
        id: check
        uses: MathieuMoalic/action-python-package-new-version@v3
        with:
          path: src/my_project/pyproject.toml # OPTIONAL: default = pyproject.toml
          indexes: pypi.org test.pypi.org index.private.org # OPTIONAL: default = pypi.org

  build-and-publish:
    needs: check-version
    runs-on: ubuntu-latest
    if: ${{ needs.check-version.outputs.exists == 'false' && !contains(needs.check-version.outputs.version, 'dev') }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup uv
        uses: astral-sh/setup-uv@v6

      - name: Build distributions
        run: uv build

      - name: Upload to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

---

## ➡️ Inputs

| Input     | Required | Default          | Description                                                                                                                     |
| --------- | -------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `path`    | no       | `pyproject.toml` | Path to the file that contains `project.name` & `project.version`.                                                              |
| `indexes` | no       | `pypi.org`       | Space-separated list of index **host names** (e.g. `pypi.org test.pypi.org index.private.org`). |

---

### Per-index environment variables

After the step runs you’ll find vars like

```
CURRENT_VERSION_EXISTS_ON_pypi_org=true
CURRENT_VERSION_EXISTS_ON_test_pypi_org=false
PACKAGE_VERSION=1.2.3

````

Use them downstream, e.g.:

```yaml
- name: Publish to PyPI
  if: env.CURRENT_VERSION_EXISTS_ON_pypi_org == 'false'
  uses: pypa/gh-action-pypi-publish@release/v1
```

Possible values:

| Value                   | Meaning                                                   |
| ----------------------- | --------------------------------------------------------- |
| `true`                  | the declared version is **already present** on that index |
| `false`                 | the version is **missing** – you may want to upload it    |
| `unknown-network-error` | the registry couldn’t be contacted                        |



---

## 🔍 How it works (internally)

* **`entrypoint.py`**

  * Uses `tomllib`/`tomli` to parse the TOML.
  * Calls each index’s JSON API (`https://<index>/pypi/<package>/json`).
  * Writes environment variables to both *stdout* (for log visibility) and `$GITHUB_ENV`.
* **Composite Action** (`action.yml`)

  * Runs the Python script.
  * Collects variables into official Action outputs.
