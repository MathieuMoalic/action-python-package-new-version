# action-python-package-new-version

## Description
Parses the pyproject.toml file to retrieve the current version and package name of your project.

Fetch Published Version from PyPI: Queries PyPI to find the latest published version of your package.

Compare Versions and Determine Publishing Need: Compares the local version from pyproject.toml with the versions available on PyPI. If the local version is not found, it sets an environment variable `NEW_VERSION=true` indicating that a new version of the package needs to be published.

Robust Error Handling: The script includes error handling for each critical step, ensuring clarity and reliability in the publishing process.

This action is particularly useful for automating the workflow of Python package development, where consistent and error-free publishing to PyPI is critical.

## Usage
Below is a sample workflow that shows how to use action-python-package-new-version:

```yaml
name: Example Workflow
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      id-token: write # IMPORTANT: this permission is mandatory for trusted publishing

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Python Package New Version
        uses: MathieuMoalic/action-python-package-new-version@v1.0.1
                        
      - name: Set up Python
        if: env.PUBLISHING == 'true'
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Build package
        if: env.PUBLISHING == 'true'
        run: python -m pip install --upgrade pip && pip install build && python -m build

      - name: Publish package distributions to PyPI
        if: env.PUBLISHING == 'true'
        uses: pypa/gh-action-pypi-publish@release/v1
```

## Outputs
- `NEW_VERSION`: set to `true` if the version in `pyproject.toml` is not published on pypi.org.

Project Link: [https://github.com/MathieuMoalic/action-python-package-new-version](https://github.com/MathieuMoalic/action-python-package-new-version)
