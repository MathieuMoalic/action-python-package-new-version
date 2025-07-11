# 🐍 Python Package Version Check • GitHub Action

Make your pipeline *self-aware*: this action inspects the `project.version` declared in **`pyproject.toml`** and tells you whether that exact version is already on the Python package index of your choice (PyPI, Test PyPI, a private index, …).

---

## 🚀 What the action does

1. **Parses** `project.name` and `project.version` from the given `pyproject.toml`.
2. **Queries** the (single) index host you specify — defaults to **`pypi.org`**.
3. **Compares** your local version with the versions already published.
4. **Exposes** three easy-to-consume outputs so you can branch your workflow logic.

---

## 🛠 Quick start

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
      current_version_exists: ${{ steps.version_check.outputs.current_version_exists }}
      version:        ${{ steps.version_check.outputs.package_version }}
      package_name:   ${{ steps.version_check.outputs.package_name }}
    steps:
      - uses: actions/checkout@v4

      - name: Check if this version already exists on PyPI
        id: version_check
        uses: your-org/python-package-version-check@v4
        with:
          # optional – default shown
          path:  pyproject.toml
          index: pypi.org

  build-and-upload:
    needs: check-version
    if: ${{ needs.check-version.outputs.current_version_exists == 'false' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python build toolchain
        uses: astral-sh/setup-uv@v6

      - name: Build sdists/wheels
        run: uv build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

> **Tip**
> Guarding your publish step with
> `if: needs.check-version.outputs.current_version_exists == 'false'`
> avoids accidental re-uploads and noisy failures.

---

## ➡️ Inputs

| Name    | Required? | Default          | Purpose                                                             |
| ------- | --------- | ---------------- | ------------------------------------------------------------------- |
| `path`  | No        | `pyproject.toml` | File that contains `project.name` and `project.version`.            |
| `index` | No        | `pypi.org`       | **Host name** of the package index to query (e.g. `test.pypi.org`). |

---

## ⬅️ Outputs

| Output                   | Example          | Description                                                         |
| ------------------------ | ---------------- | ------------------------------------------------------------------- |
| `current_version_exists` | `true` / `false` | **`true`** if the version is already published on the chosen index. |
| `package_version`        | `1.4.2`          | The version string read from `pyproject.toml`.                      |
| `package_name`           | `awesome-utils`  | The package name read from `pyproject.toml`.                        |

---

## 🧩 How it works under the hood

| Component           | Role                                                                                                                                                                                                |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`entrypoint.py`** | • Parses TOML with `tomllib`/`tomli` (Py≥3.11 / <3.11) <br>• GETs `https://<index>/pypi/<name>/json` <br>• Emits results via `echo "::set-output …"` so the composite step can surface them to you. |
| **`action.yml`**    | • Defines the two configurable inputs <br>• Wraps the Python script inside a composite action <br>• Maps script output variables to the three official action outputs.                              |

---

## 📚 Example patterns

* **Skip CI** when the tag already exists:

  ```yaml
  if: ${{ steps.version_check.outputs.current_version_exists == 'true' }}
  ```

* **Add a “DEV” suffix** to nightly builds unless you’re on `main`:

  ```yaml
  - run: echo "VERSION=$(python scripts/bump.py)" >> $GITHUB_ENV
    if: github.ref != 'refs/heads/main'
  ```

---

## 🏷️ Version compatibility

* Requires **Python 3.8+** in the runner.
* Works with **PEP 621-style** `pyproject.toml` (`[project]` table).

---

## 📄 License

This action is released under the **MIT License** – see [`LICENSE`](LICENSE) for details.

Happy shipping! 🎉
