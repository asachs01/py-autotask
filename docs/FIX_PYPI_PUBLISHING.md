# Fix PyPI Trusted Publishing

## Issue
The PyPI publishing is failing with:
```
Token request failed: the server refused the request for the following reasons:
* `invalid-publisher`: valid token, but no corresponding publisher
```

## Solution

You need to configure trusted publishing on PyPI. Here's how:

### 1. Go to PyPI
Navigate to https://pypi.org/manage/project/py-autotask/settings/publishing/

### 2. Add GitHub Publisher
Click "Add a publisher" and configure:

- **Owner**: `asachs01`
- **Repository name**: `py-autotask`
- **Workflow name**: `release.yml`
- **Environment name**: `pypi` (this must match the `environment: pypi` in the workflow)

### 3. Save Configuration
Click "Add" to save the trusted publisher configuration.

### Alternative: Use API Token

If you prefer to use an API token instead of trusted publishing:

1. Generate a PyPI API token at https://pypi.org/manage/account/token/
2. Add it as a GitHub secret named `PYPI_API_TOKEN` in your repository
3. Update the workflow to use the token:

```yaml
publish-pypi:
  name: Publish to PyPI
  runs-on: ubuntu-latest
  needs: [release]
  steps:
    - name: Download artifacts
      uses: actions/download-artifact@v4
      with:
        name: dist
        path: dist/
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
        print-hash: true
        verbose: true
```

## Recommended: Use Trusted Publishing

Trusted publishing is more secure and doesn't require managing API tokens. It's the recommended approach for GitHub Actions.

## Re-run Release

After configuring trusted publishing, you can:

1. Re-run the failed workflow from the Actions tab
2. Or create a new release tag to trigger a fresh release

## References
- [PyPI Trusted Publishers Documentation](https://docs.pypi.org/trusted-publishers/)
- [Troubleshooting Guide](https://docs.pypi.org/trusted-publishers/troubleshooting/)
- [GitHub OIDC for PyPI](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)