# Version Management and Branching Strategy

This document outlines the version management and branching strategy for the LLM Assistant Framework project.

## Semantic Versioning

We use Semantic Versioning (SemVer) for our releases. The format is MAJOR.MINOR.PATCH (e.g., 1.0.0, 1.1.0, 1.1.1).

## Branching Strategy

```
main (latest stable release)
|
├── develop (integration branch for next release)
|   |
|   ├── feature/v1.1.0-new-feature
|   └── bugfix/v1.0.1-bug-fix
|
├── release/v1.0.x (maintenance branch for v1.0.x)
|   └── hotfix/v1.0.2-critical-fix
|
└── release/v1.1.x (maintenance branch for v1.1.x)
```

- `main`: Contains the latest stable release.
- `develop`: Integration branch for the next release.
- `feature/*` and `bugfix/*`: Create these branches from `develop` for new features and bug fixes.
- `release/v1.0.x`, `release/v1.1.x`, etc.: Maintenance branches for each major or minor version.
- `hotfix/*`: For critical bugs that need to be fixed in the current release.

## Working on Changes

### For V1 changes after release:

1. Create a `release/v1.0.x` branch if it doesn't exist.
2. For bug fixes, create a `bugfix/v1.0.1-description` branch from `release/v1.0.x`.
3. Make changes, test, and merge back into `release/v1.0.x`.
4. Merge `release/v1.0.x` into `main` and tag the new release (e.g., v1.0.1).

### For V2 (new major version):

1. Create a `feature/v2.0.0-description` branch from `develop`.
2. Implement new features and breaking changes.
3. Merge into `develop` when ready.
4. Create a `release/v2.0.x` branch from `develop`.
5. Perform final testing and bug fixes on `release/v2.0.x`.
6. Merge `release/v2.0.x` into `main` and tag the new release (v2.0.0).

## Publishing Releases

1. Update the version in `setup.py`:

```python
setup(
    name="assinstants",
    version="X.Y.Z",  # Update this for each release
    ...
)
```

2. Tag your releases on GitHub:

   ```
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   git push origin vX.Y.Z
   ```

3. Create a GitHub Release with release notes.

4. Publish to PyPI:
   ```
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```

By following this strategy, we can maintain multiple versions, work on new features, and provide a clear upgrade path for users.
