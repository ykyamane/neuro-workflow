# Git Workflow Guide for Neuro-Workflow

## Overview

You now have a branch `feature/enhanced-version` on GitHub (`oist/neuro-workflow`). This guide explains how to work with your local code and keep it synchronized with GitHub.

## Basic Workflow

### 1. Push Local Changes to GitHub

When you make changes locally and want to update GitHub:

```bash
# Make your changes locally (edit files, etc.)

# Stage your changes
git add .

# Commit your changes
git commit -m "Description of your changes"

# Push to GitHub
git push upstream feature/enhanced-version-20251203:feature/enhanced-version
# Or if you've set up tracking:
git push upstream feature/enhanced-version-20251203
```

**What happens:**
- Your local changes are uploaded to GitHub
- Your branch on GitHub is updated
- Others can see your changes (if they have access)

### 2. Pull Changes from GitHub to Local

If you (or someone else) made changes on GitHub and you want to update your local code:

```bash
# Fetch latest changes from GitHub
git fetch upstream

# Pull changes into your local branch
git pull upstream feature/enhanced-version
```

**What happens:**
- Your local code is updated with changes from GitHub
- If there are conflicts, Git will ask you to resolve them

### 3. Check Status

See what's different between local and GitHub:

```bash
# Check if you have uncommitted changes
git status

# See commits that are on GitHub but not locally
git log HEAD..upstream/feature/enhanced-version

# See commits that are local but not on GitHub
git log upstream/feature/enhanced-version..HEAD
```

## Common Scenarios

### Scenario 1: You Made Local Changes

```bash
# 1. Check what changed
git status

# 2. Stage changes
git add .

# 3. Commit
git commit -m "Added new feature X"

# 4. Push to GitHub
git push upstream feature/enhanced-version-20251203:feature/enhanced-version
```

### Scenario 2: You Want to Get Latest from GitHub

```bash
# 1. Fetch latest
git fetch upstream

# 2. Pull changes
git pull upstream feature/enhanced-version

# 3. If there are conflicts, resolve them, then:
git add .
git commit -m "Merged changes from GitHub"
```

### Scenario 3: You Made Changes Both Locally and on GitHub

This creates a situation where you need to merge:

```bash
# 1. Fetch latest from GitHub
git fetch upstream

# 2. Try to pull (Git will attempt to merge)
git pull upstream feature/enhanced-version

# 3. If there are conflicts:
#    - Git will mark conflicted files
#    - Edit files to resolve conflicts
#    - Stage resolved files: git add .
#    - Complete merge: git commit
```

### Scenario 4: You Want to Replace Local with GitHub Version

⚠️ **Warning: This discards local changes!**

```bash
# 1. Fetch latest
git fetch upstream

# 2. Reset local branch to match GitHub exactly
git reset --hard upstream/feature/enhanced-version
```

**Use this only if:**
- You're sure you want to discard local changes
- You've backed up anything important
- You want to start fresh from GitHub

## Setting Up Branch Tracking (Optional)

To make pushing/pulling easier, you can set up tracking:

```bash
# Set upstream tracking
git branch --set-upstream-to=upstream/feature/enhanced-version feature/enhanced-version-20251203

# Now you can just use:
git push
git pull
```

## Syncing with Upstream Repository

When the original `oist/neuro-workflow` repository gets updates, you can merge them:

```bash
# Use the sync script
./sync_with_upstream.sh

# Or manually:
git fetch upstream
git merge upstream/main -X theirs
# Resolve any conflicts
git push upstream feature/enhanced-version-20251203:feature/enhanced-version
```

## Best Practices

1. **Commit Often**: Small, frequent commits are easier to manage
2. **Pull Before Push**: Always pull before pushing to avoid conflicts
3. **Write Good Commit Messages**: Describe what and why, not just what
4. **Test Before Push**: Make sure your code works before pushing
5. **Backup Important Work**: Before major operations, create a backup branch

## Quick Reference

```bash
# Push local → GitHub
git push upstream feature/enhanced-version-20251203:feature/enhanced-version

# Pull GitHub → Local
git pull upstream feature/enhanced-version

# Check differences
git status
git diff

# See commit history
git log --oneline -10

# Create backup branch
git branch backup-$(date +%Y%m%d)
```

## Troubleshooting

### "Your branch is ahead of 'upstream/feature/enhanced-version'"
- You have local commits not on GitHub
- Push them: `git push upstream feature/enhanced-version-20251203:feature/enhanced-version`

### "Your branch is behind 'upstream/feature/enhanced-version'"
- GitHub has commits you don't have locally
- Pull them: `git pull upstream feature/enhanced-version`

### "Merge conflict"
- Git can't automatically merge changes
- Edit conflicted files (look for `<<<<<<<`, `=======`, `>>>>>>>`)
- Stage resolved files: `git add .`
- Complete merge: `git commit`

### "Authentication failed"
- Use Personal Access Token (PAT) instead of password
- Or set up SSH keys for easier authentication

