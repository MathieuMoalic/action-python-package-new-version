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
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: action-python-package-new-version
      uses: MathieuMoalic/action-python-package-new-version@v1
```

## Outputs
- `NEW_VERSION`: set to `true` if the version in `pyproject.toml` is not published on pypi.org.

Project Link: [https://github.com/MathieuMoalic/action-python-package-new-version](https://github.com/MathieuMoalic/action-python-package-new-version)
