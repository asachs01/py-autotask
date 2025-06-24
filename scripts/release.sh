#!/bin/bash
# Release helper script for py-autotask
# Usage: ./scripts/release.sh <version> [--dry-run]

set -e

VERSION=$1
DRY_RUN=${2:-""}

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [--dry-run]"
    echo "Example: $0 1.0.0"
    echo "Example: $0 1.0.0-beta.1"
    exit 1
fi

# Validate version format
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+(\.[0-9]+)?)?$ ]]; then
    echo "Error: Invalid version format. Use semantic versioning (e.g., 1.0.0, 1.0.0-beta.1)"
    exit 1
fi

echo "🚀 Preparing release for py-autotask v$VERSION"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: You're not on the main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ Error: You have uncommitted changes. Please commit or stash them first."
    exit 1
fi

# Check if tag already exists
if git tag -l | grep -q "^v$VERSION$"; then
    echo "❌ Error: Tag v$VERSION already exists"
    exit 1
fi

# Check if CHANGELOG has entry for this version
if ! grep -q "## \[$VERSION\]" CHANGELOG.md; then
    echo "⚠️  Warning: No changelog entry found for version $VERSION"
    echo "Please add a changelog entry in the format:"
    echo "## [$VERSION] - $(date +%Y-%m-%d)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run tests
echo "🧪 Running tests..."
if [ "$DRY_RUN" != "--dry-run" ]; then
    python -m pytest tests/ -v -m "not integration and not performance" --tb=short
fi

# Run linting
echo "🔍 Running code quality checks..."
if [ "$DRY_RUN" != "--dry-run" ]; then
    python -m black --check py_autotask tests
    python -m isort --check-only py_autotask tests
    python -m flake8 py_autotask tests --max-line-length=88 --extend-ignore=E203,W503
fi

# Create tag
echo "🏷️  Creating tag v$VERSION..."
if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "DRY RUN: Would create tag v$VERSION"
else
    git tag -a "v$VERSION" -m "Release version $VERSION"
fi

# Push tag
echo "📤 Pushing tag to origin..."
if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "DRY RUN: Would push tag v$VERSION"
else
    git push origin "v$VERSION"
fi

echo "✅ Release process initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Monitor GitHub Actions workflow: https://github.com/asachs01/py-autotask/actions"
echo "2. Check GitHub release: https://github.com/asachs01/py-autotask/releases/tag/v$VERSION"
echo "3. Verify PyPI publication: https://pypi.org/project/py-autotask/$VERSION/"
echo ""

if [[ $VERSION == *"beta"* ]] || [[ $VERSION == *"rc"* ]] || [[ $VERSION == *"alpha"* ]]; then
    echo "🧪 Pre-release detected - will publish to Test PyPI"
    echo "   Test PyPI: https://test.pypi.org/project/py-autotask/$VERSION/"
else
    echo "🎉 Production release - will publish to PyPI"
fi 