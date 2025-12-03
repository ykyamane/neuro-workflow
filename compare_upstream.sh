#!/bin/bash
# Script to compare local code with upstream repository

set -e

REPO_DIR="/Users/kirill/Documents/digital_brain/neuro-workflow"
UPSTREAM_URL="https://github.com/oist/neuro-workflow"

echo "=========================================="
echo "Upstream Comparison Report"
echo "=========================================="
echo ""

cd "$REPO_DIR"

# Fetch latest
echo "Fetching latest from upstream..."
git fetch origin

# Show commits we're missing
echo ""
echo "=========================================="
echo "NEW COMMITS IN UPSTREAM (not in your code):"
echo "=========================================="
git log --oneline HEAD..origin/main

# Show files that changed
echo ""
echo "=========================================="
echo "FILES CHANGED IN UPSTREAM:"
echo "=========================================="
git diff --name-status HEAD origin/main

# Show detailed changes for key files
echo ""
echo "=========================================="
echo "DETAILED CHANGES IN KEY FILES:"
echo "=========================================="

# Check if we have local modifications to these files
echo ""
echo "Files you modified that also changed upstream:"
git diff --name-only HEAD origin/main | while read file; do
    if git diff --quiet HEAD -- "$file" 2>/dev/null; then
        : # File not modified locally
    else
        echo "  CONFLICT RISK: $file"
    fi
done

# Summary
echo ""
echo "=========================================="
echo "SUMMARY:"
echo "=========================================="
echo "Your last commit: $(git log -1 --format='%h %s' HEAD)"
echo "Upstream latest:  $(git log -1 --format='%h %s' origin/main)"
echo "Commits behind:  $(git rev-list --count HEAD..origin/main)"
echo "Commits ahead:   $(git rev-list --count origin/main..HEAD)"

