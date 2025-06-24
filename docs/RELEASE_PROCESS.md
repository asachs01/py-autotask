# Release Process

This document outlines the automated release process for py-autotask using GitHub Actions.

## Overview

The release process is fully automated using GitHub Actions and is triggered when you push a version tag to the repository. The workflow handles:

1. **Quality Assurance**: Runs tests and linting
2. **Package Building**: Creates source and wheel distributions
3. **GitHub Release**: Creates a GitHub release with changelog notes
4. **PyPI Publishing**: Publishes to PyPI using trusted publishing
5. **Post-Release Tasks**: Creates tracking issues and notifications

## Release Workflow

### Prerequisites

1. **PyPI Trusted Publishing**: Configure trusted publishing on PyPI
   - Go to [PyPI Trusted Publishing](https://pypi.org/manage/account/publishing/)
   - Add py-autotask project with GitHub repository details
   - Configure environment name: `pypi`

2. **GitHub Environments**: Set up GitHub environments
   - `pypi`: For production PyPI releases
   - `test-pypi`: For test PyPI releases (pre-releases)

3. **Repository Secrets**: No API tokens needed with trusted publishing!

### Creating a Release

#### 1. Prepare the Release

```bash
# Ensure you're on main branch with latest changes
git checkout main
git pull origin main

# Update CHANGELOG.md with new version section
# Follow the format: ## [X.Y.Z] - YYYY-MM-DD
```

#### 2. Update Version

The project uses `setuptools_scm` for automatic versioning based on Git tags. No manual version updates needed in code!

#### 3. Create and Push Tag

```bash
# Create annotated tag (recommended)
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tag to trigger release workflow
git push origin v1.0.0
```

#### 4. Monitor Release

1. **GitHub Actions**: Watch the workflow at `https://github.com/your-username/py-autotask/actions`
2. **Release Creation**: Check releases at `https://github.com/your-username/py-autotask/releases`
3. **PyPI Publication**: Verify at `https://pypi.org/project/py-autotask/`

## Release Types

### Production Release

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

- Publishes to production PyPI
- Creates full GitHub release
- Runs all quality checks

### Pre-Release (Beta/RC/Alpha)

```bash
git tag -a v1.0.0-beta.1 -m "Beta release 1.0.0-beta.1"
git push origin v1.0.0-beta.1
```

- Publishes to Test PyPI only
- Marked as pre-release on GitHub
- Useful for testing before production

## Workflow Jobs

### 1. Test Suite
- Runs unit tests (excluding integration/performance)
- Generates coverage reports
- Must pass for release to continue

### 2. Code Quality
- Black code formatting check
- isort import sorting check
- flake8 linting
- mypy type checking

### 3. Build Distribution
- Creates source distribution (`.tar.gz`)
- Creates wheel distribution (`.whl`)
- Validates distributions with twine
- Uploads as workflow artifacts

### 4. Create GitHub Release
- Extracts changelog section for version
- Creates GitHub release with artifacts
- Marks pre-releases appropriately
- Uses semantic versioning detection

### 5. Publish to PyPI
- Uses trusted publishing (no API tokens!)
- Publishes to production PyPI
- Only runs for production releases

### 6. Publish to Test PyPI
- Publishes pre-releases to test.pypi.org
- Allows testing installation before production
- Only runs for beta/rc/alpha tags

### 7. Post-Release Tasks
- Creates tracking issue for release
- Includes installation instructions
- Provides links to release and PyPI

## Changelog Format

The workflow automatically extracts release notes from `CHANGELOG.md`. Use this format:

```markdown
## [1.0.0] - 2025-06-23

### Added
- New feature descriptions

### Changed
- Modified feature descriptions

### Fixed
- Bug fix descriptions

### Removed
- Removed feature descriptions
```

## Troubleshooting

### Failed Release

If a release fails:

1. **Check workflow logs**: Identify the failing step
2. **Fix issues**: Address code quality or test failures
3. **Delete tag**: `git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0`
4. **Recreate tag**: After fixes, create tag again

### PyPI Publishing Issues

1. **Trusted Publishing**: Ensure PyPI trusted publishing is configured
2. **Environment Names**: Verify GitHub environment names match PyPI config
3. **Permissions**: Check workflow has `id-token: write` permission

### Missing Release Notes

If changelog extraction fails, the workflow falls back to a generic message. Ensure:

1. **Version Format**: Use `## [X.Y.Z] - YYYY-MM-DD` format
2. **Exact Match**: Version in changelog matches tag (without 'v' prefix)
3. **Valid Markdown**: Proper markdown formatting

## Best Practices

1. **Test First**: Always test changes thoroughly before tagging
2. **Semantic Versioning**: Follow [semver.org](https://semver.org) guidelines
3. **Changelog Updates**: Update changelog before creating tag
4. **Pre-releases**: Use beta/rc versions for testing
5. **Monitor**: Watch the workflow and verify successful publication

## Version Strategy

- **Major**: Breaking changes (v2.0.0)
- **Minor**: New features, backward compatible (v1.1.0)
- **Patch**: Bug fixes, backward compatible (v1.0.1)
- **Pre-release**: Testing versions (v1.0.0-beta.1)

## Examples

```bash
# Major release
git tag -a v2.0.0 -m "Major release with breaking changes"

# Minor release  
git tag -a v1.1.0 -m "New features and improvements"

# Patch release
git tag -a v1.0.1 -m "Bug fixes and security updates"

# Beta release
git tag -a v1.1.0-beta.1 -m "Beta testing for v1.1.0"

# Release candidate
git tag -a v2.0.0-rc.1 -m "Release candidate for v2.0.0"
```

The automated workflow ensures consistent, reliable releases while maintaining high quality standards through automated testing and validation. 