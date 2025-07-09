# Python Package Version Check – GitHub Action

Quickly find out whether the version declared in your `pyproject.toml` is **already published** to one or more Python package indexes (PyPI, Test PyPI, a private index, …).
The action sets convenient outputs you can use to decide whether you need to run a `build` + `twine upload` step.

---

## 📦 What it does

1. Reads **`project.name`** and **`project.version`** from the supplied `pyproject.toml`.
2. Queries each index you specify (defaults to `pypi.org`).
3. Compares the local version against the list of released versions.
4. Exposes result flags via:

   * **environment variables** (for debugging inside the step)
   * **composite-action outputs** `publishing`, `package_version`, `package_name`

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
        id: version-check
        uses: your-org/python-package-version-check@v1
        with:
          # Optional – location of pyproject.toml if not at repo root
          path: src/my_project/pyproject.toml
          
          # Optional – space- or newline-separated list of index host names
          # Example below checks PyPI, TestPyPI, and a private index
          indexes: |
            pypi.org
            test.pypi.org
            packages.my-company.local

      - name: Publish to indexes when needed
        if: steps.version-check.outputs.publishing == 'true'
        run: |
          python -m build
          twine upload --repository pypi dist/*
```

---

## ➡️ Inputs

| Input     | Required | Default          | Description                                                                                                                     |
| --------- | -------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `path`    | no       | `pyproject.toml` | Path to the file that contains `project.name` & `project.version`.                                                              |
| `indexes` | no       | *(built-in)*     | Space- or newline-separated list of index **host names** (e.g. `pypi.org`). Leave blank to query the default list (`pypi.org`). |

---

## ⬅️ Outputs

| Output            | Type   | Meaning                                                         |
| ----------------- | ------ | --------------------------------------------------------------- |
| `publishing`      | bool   | `true` ⇒ the version is missing from **all** reachable indexes. |
| `package_version` | string | The version found in `pyproject.toml`.                          |
| `package_name`    | string | The package name found in `pyproject.toml`.                     |

### Per-index environment variables

Within the same composite step you also have:

* `PUBLISHING_<index>` – e.g. `PUBLISHING_pypi_org=true`
  (`index` dots replaced by underscores)

These are **not** exported as formal action outputs, but you can consume them in subsequent shell commands inside the same composite Action if you need per-index logic.

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
