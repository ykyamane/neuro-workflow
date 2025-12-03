#!/bin/bash
# Routine script to sync with upstream repository
# This script safely merges upstream changes without affecting the original repository

set -e  # Exit on error

REPO_DIR="/Users/kirill/Documents/digital_brain/neuro-workflow"
UPSTREAM_REMOTE="upstream"
YOUR_BRANCH="main"  # Change this to your working branch name

cd "$REPO_DIR"

echo "=========================================="
echo "Syncing with Upstream Repository"
echo "=========================================="
echo ""

# Step 1: Check current status
echo "Step 1: Checking current status..."
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "WARNING: You have uncommitted changes!"
    echo "Please commit or stash them before syncing."
    echo ""
    echo "To commit: git add . && git commit -m 'Your message'"
    echo "To stash: git stash"
    exit 1
fi

# Step 2: Ensure upstream remote is configured
echo "Step 2: Checking upstream remote..."
if ! git remote | grep -q "^${UPSTREAM_REMOTE}$"; then
    echo "Setting up upstream remote..."
    git remote add upstream https://github.com/oist/neuro-workflow.git
fi

# Step 3: Fetch latest from upstream
echo "Step 3: Fetching latest from upstream..."
git fetch upstream

# Step 4: Check if there are updates
LOCAL_COMMIT=$(git rev-parse HEAD)
UPSTREAM_COMMIT=$(git rev-parse upstream/main)

if [ "$LOCAL_COMMIT" = "$UPSTREAM_COMMIT" ]; then
    echo "✓ Already up to date with upstream!"
    exit 0
fi

COMMITS_BEHIND=$(git rev-list --count HEAD..upstream/main)
echo "Found $COMMITS_BEHIND new commits in upstream"

# Step 5: Show what's coming
echo ""
echo "Recent upstream commits:"
git log --oneline HEAD..upstream/main | head -10

# Step 6: Create backup branch
BACKUP_BRANCH="backup-before-sync-$(date +%Y%m%d-%H%M%S)"
echo ""
echo "Step 4: Creating backup branch: $BACKUP_BRANCH"
git branch "$BACKUP_BRANCH"

# Step 7: Merge upstream
echo ""
echo "Step 5: Merging upstream changes..."
echo "Using strategy: prefer upstream changes for conflicts"
if git merge upstream/main -m "Merge upstream changes from oist/neuro-workflow" -X theirs; then
    echo "✓ Merge completed successfully!"
else
    # Merge had conflicts even with -X theirs (can happen with add/add conflicts)
    
    echo ""
    echo "=========================================="
    echo "CONFLICTS DETECTED"
    echo "=========================================="
    echo ""
    echo "Conflicted files:"
    git diff --name-only --diff-filter=U
    echo ""
    echo "To resolve conflicts:"
    echo "1. Review conflicted files"
    echo "2. Edit files to resolve conflicts (upstream takes priority)"
    echo "3. Run: git add <resolved-files>"
    echo "4. Run: git commit"
    echo ""
    echo "Or to abort: git merge --abort"
    echo ""
    echo "To resolve automatically (prefer upstream):"
    echo "  git checkout --theirs <conflicted-file>"
    echo "  git add <conflicted-file>"
    echo "  git commit"
    exit 1
fi

# Step 8: Check for remaining conflicts (in case -X theirs didn't handle everything)
if git diff --check; then
    echo ""
    echo "WARNING: There may still be conflict markers in files!"
    echo "Please review and resolve manually."
fi

# Step 9: Success message
echo ""
echo "=========================================="
echo "✓ Successfully merged upstream changes!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review any conflict resolutions"
echo "2. Test your code: docker-compose -f gui/docker-compose.yml up -d"
echo "3. Run your test suite"
echo "4. If everything works, push to your branch:"
echo "   git push origin $(git branch --show-current)"
echo ""

