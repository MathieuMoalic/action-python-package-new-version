# Python Package Version Check – GitHub Action

Quickly find out whether the version declared in your `pyproject.toml` is **already published** to one or more Python package indexes (PyPI, Test PyPI, a private index, …).

---

## 📦 What it does

1. Reads **`project.name`** and **`project.version`** from the supplied `pyproject.toml`.
2. Queries each index you specify (defaults to `pypi.org`).
3. Compares the local version against the list of released versions.
4. Exposes result flags via:

   * **environment variables** (for debugging inside the step)

If the version is missing from *all* available indexes, `publishing` is set to `true`.

---

## 🛠 Usage

```yaml
name: Build & Publish

on:
  push:
    branches: [ "main" ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check whether this version is already published
        uses: MathieuMoalic/action-python-package-new-version@v2.0.1
        with:
          # Optional – location of pyproject.toml if not at repo root
          path: src/my_project/pyproject.toml
          
          # Optional – space-separated list of index host names
          # Example below checks PyPI, TestPyPI, and a private index
          indexes: pypi.org test.pypi.org index.private.org

      # This is how you can access it through env, for individual indexes
      - name: Install uv
        if: env.PUBLISHING_pypi_org == 'true'
        uses: astral-sh/setup-uv@v6

      - name: Build package
        if: env.PUBLISHING_pypi_org == 'true'
        run: uv build

      - name: Publish package distributions to PyPI
        if: env.PUBLISHING_pypi_org == 'true'
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

Within the same composite step you also have:

* `PUBLISHING_<index>` – e.g. `PUBLISHING_pypi_org=true`
  (`index` dots replaced by underscores)

---

## 🔍 How it works (internally)

* **`entrypoint.py`**

  * Uses `tomllib`/`tomli` to parse the TOML.
  * Calls each index’s JSON API (`https://<index>/pypi/<package>/json`).
  * Writes environment variables to both *stdout* (for log visibility) and `$GITHUB_ENV`.
* **Composite Action** (`action.yml`)

  * Runs the Python script.
  * Collects variables into official Action outputs.

---

## ❓ FAQ

**Q: I use TestPyPI – how do I ignore its result?**
A: Pass only the indexes you care about in `indexes:`. If you list both PyPI and TestPyPI, `publishing` turns `false` as soon as the version exists on either index.

**Q: My workflow failed because an index was down.**
A: Temporary network errors set `PUBLISHING_<index>` to `true` but do **not** influence the global `publishing` flag. The script treats the index as “unavailable” rather than “needs publishing”, so your upload step won’t run solely due to downtime.
