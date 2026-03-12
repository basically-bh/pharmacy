# Pharmacy Development Workflow

## Branch Model

- `main`: stable releases only
- `develop`: active development
- feature work: branch from `develop`
- releases: merge `develop` into `main` and tag a version

## Expected Workflow

1. Create or update feature branches from `develop`.
2. Merge completed feature work back into `develop`.
3. When ready for a stable release, merge `develop` into `main`.
4. Tag the release on `main` with the next version.

## Example

- feature work -> `develop`
- release -> merge `develop` -> `main` -> tag version
