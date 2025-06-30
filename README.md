# action-python-package-new-version

Automatically detects whether the version declared in **pyproject.toml** has
already been published on one **or many** Python package indexes.

## 🔍 What it does

1. **Parse `pyproject.toml`** – extracts `name` and `version`.  
2. **Query each index** (`pypi.org`, `test.pypi.org`, a private mirror, …).  
3. **Export booleans**  
   * `PUBLISHING_<index>` – `true` if that registry **does not** have the
     version.  
   * Aggregate `PUBLISHING` – `true` *only* if **none** of the indexes have it.  
4. Also exports `PACKAGE_NAME` and `PACKAGE_VERSION`.

These variables let the rest of your workflow decide **where** to upload.

## 📦 Inputs

| Name    | Default              | Description |
|---------|----------------------|-------------|
| `path`  | `pyproject.toml`     | Path to the project’s `pyproject.toml`. |
| `indexes` | *(empty)* → `pypi.org test.pypi.org` | Space-separated host-names to check. |

## 🛠 Outputs

| Output                      | Example | Meaning |
|-----------------------------|---------|---------|
| `publishing`                | `true`  | Same as `$PUBLISHING`. |
| `package_version`           | `1.4.2` | Version from `pyproject.toml`. |
| `package_name`              | `my_pkg`| Name from `pyproject.toml`. |
| `publishing_pypi_org`       | `false` | Version already on PyPI. |
| `publishing_test_pypi_org`  | `true`  | Version **not** on Test PyPI. |

*(Index-specific outputs are created dynamically; replace dots with underscores.)*

## 🚀 Usage

### Check **PyPI only** (back-compatible behaviour)

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Version check
    uses: MathieuMoalic/action-python-package-new-version@v1.1.0
    with:
      path: pyproject.toml            # optional, shown for clarity
      indexes: "pypi.org"             # ← only look at the real PyPI

  - name: Build
    if: env.PUBLISHING_pypi_org == 'true'
    run: uv build

  - name: Publish to PyPI
    if: env.PUBLISHING_pypi_org == 'true'
    uses: pypa/gh-action-pypi-publish@release/v1
