# Upstream Sync Routine - Complete Guide

## Overview

This document describes the routine process for keeping your enhanced version of NeuroWorkflow synchronized with the upstream repository (https://github.com/oist/neuro-workflow) while maintaining your own enhancements.

## Key Principles

1. **Never modify upstream directly** - All changes go to your own branch
2. **Prefer upstream changes** - When conflicts occur, upstream takes priority unless there are fundamental flaws
3. **Maintain your enhancements** - Your additions (parameter metadata, SnakeMake, job managers) are preserved
4. **Test before pushing** - Always verify the merged code works

## Repository Setup

### Current Configuration

- **Upstream remote**: `upstream` → https://github.com/oist/neuro-workflow
- **Your working branch**: `feature/enhanced-version-YYYYMMDD` (or your custom branch)
- **Backup branch**: Created automatically before each merge

### Setting Up Your Own GitHub Remote

To push your code to GitHub without affecting upstream:

**Option 1: Fork the Repository (Recommended)**

1. Go to https://github.com/oist/neuro-workflow
2. Click "Fork" button (top right)
3. This creates your own copy at `https://github.com/YOUR_USERNAME/neuro-workflow`

4. Add your fork as a remote:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/neuro-workflow.git
   ```

**Option 2: Create Your Own Repository**

1. Create a new repository on GitHub (e.g., `neuro-workflow-enhanced`)
2. Add it as a remote:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/neuro-workflow-enhanced.git
   ```

**Verify Setup**:
```bash
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/... (fetch)
# origin    https://github.com/YOUR_USERNAME/... (push)
# upstream  https://github.com/oist/neuro-workflow (fetch)
# upstream  https://github.com/oist/neuro-workflow (push)
```

## Regular Sync Routine

### Quick Sync (Automated)

Use the provided script:

```bash
./sync_with_upstream.sh
```

This script:
- Checks for uncommitted changes
- Fetches latest from upstream
- Creates backup branch
- Merges upstream changes
- Handles conflicts (prefers upstream)

### Manual Sync (Step-by-Step)

If you prefer manual control or the script encounters issues:

#### Step 1: Save Your Work

```bash
# Check status
git status

# Commit any uncommitted changes
git add .
git commit -m "WIP: Your work description"

# Or stash if not ready to commit
git stash save "Work in progress"
```

#### Step 2: Ensure You're on Your Working Branch

```bash
# Check current branch
git branch

# Switch to your working branch if needed
git checkout feature/enhanced-version-20251203
# Or: git checkout main  # if you work on main
```

#### Step 3: Fetch Latest from Upstream

```bash
git fetch upstream
```

#### Step 4: Check What's New

```bash
# See new commits
git log HEAD..upstream/main --oneline

# See which files changed
git diff --name-status HEAD..upstream/main

# Count commits behind
git rev-list --count HEAD..upstream/main
```

#### Step 5: Create Backup (Safety Net)

```bash
git branch backup-before-sync-$(date +%Y%m%d-%H%M%S)
```

#### Step 6: Merge Upstream

```bash
# Merge with upstream (preferring upstream for conflicts)
git merge upstream/main -m "Merge upstream changes from oist/neuro-workflow"
```

#### Step 7: Resolve Conflicts (if any)

If conflicts occur:

```bash
# See conflicted files
git status

# For each conflicted file, prefer upstream version:
git checkout --theirs <file-path>
git add <file-path>

# Or manually edit files to combine both versions
# Then: git add <file-path>
```

**Conflict Resolution Strategy**:
- **Prefer upstream** unless it has fundamental flaws
- If your version fixes a critical bug upstream doesn't have, keep yours
- If both fix the same issue, prefer upstream's solution
- Document why you kept your version if you do

#### Step 8: Complete the Merge

```bash
# After resolving all conflicts
git commit -m "Merge upstream changes - resolved conflicts"
```

#### Step 9: Test

```bash
# Test Docker setup
docker-compose -f gui/docker-compose.yml down
docker-compose -f gui/docker-compose.yml up -d

# Check services
docker-compose -f gui/docker-compose.yml ps

# Test frontend
# Open http://localhost:5173

# Test backend
# Open http://localhost:3000/api

# Test JupyterHub
# Open http://localhost:8000

# Run your test suite
# python test_features_quick.py
# Or run notebooks: notebooks/Test_New_Features.ipynb
```

#### Step 10: Push to Your Repository

```bash
# Push your branch to your own repository
git push origin feature/enhanced-version-20251203

# Or if working on main:
git push origin main
```

## Conflict Resolution Guide

### Common Conflict Scenarios

#### Scenario 1: Both Fixed the Same Issue

**Example**: Both you and upstream fixed JupyterHub network configuration

**Resolution**: Prefer upstream's version
```bash
git checkout --theirs gui/workflow_backend/.../jupyterhub_config.py
git add gui/workflow_backend/.../jupyterhub_config.py
```

#### Scenario 2: Different Features

**Example**: You added parameter metadata service, upstream added workflow execution

**Resolution**: Both are kept automatically (no conflict)

#### Scenario 3: Your Fix is Critical

**Example**: Your fix prevents a crash, upstream doesn't have it

**Resolution**: Keep your version, but document why
```bash
# Manually edit file to keep your version
git checkout --ours <file-path>
git add <file-path>
# Add comment in code explaining why
```

#### Scenario 4: Both Created Same File

**Example**: Both created `chatbotView.tsx`

**Resolution**: Prefer upstream's version (usually more complete)
```bash
git checkout --theirs <file-path>
git add <file-path>
```

### Files That Commonly Conflict

Based on experience:
- `gui/docker-compose.yml` - Docker configuration
- `gui/workflow_backend/.../jupyterhub_config.py` - JupyterHub settings
- `gui/workflow_frontend/src/auth/supabase.ts` - Authentication
- `gui/workflow_frontend/src/protectedRoute.tsx` - Route protection

## Testing Checklist

After each merge, verify:

- [ ] Docker services start without errors
- [ ] Frontend loads at http://localhost:5173
- [ ] Backend API responds at http://localhost:3000/api
- [ ] JupyterHub login works
- [ ] JupyterHub spawns containers
- [ ] Workflow execution works
- [ ] Node upload works
- [ ] Your enhancements still work:
  - [ ] Parameter metadata service
  - [ ] SnakeMake generation
  - [ ] Job managers
  - [ ] Documentation accessible

## Troubleshooting

### Merge Failed - Uncommitted Changes

```bash
# Option 1: Commit changes
git add .
git commit -m "Your message"

# Option 2: Stash changes
git stash
# After merge: git stash pop
```

### Merge Created Conflicts

```bash
# See conflicts
git status

# Resolve each file
git checkout --theirs <file>  # Prefer upstream
# OR
git checkout --ours <file>    # Keep your version

# After resolving all:
git add <resolved-files>
git commit
```

### Something Broke After Merge

```bash
# Option 1: Undo merge (if not committed)
git merge --abort

# Option 2: Revert to backup
git checkout backup-before-sync-YYYYMMDD-HHMMSS

# Option 3: Reset to before merge
git reset --hard HEAD~1  # Careful: loses merge commit
```

### Upstream Has Breaking Changes

1. Check upstream's commit messages for breaking changes
2. Review their documentation/README
3. Test thoroughly before using in production
4. Consider staying on a stable commit until issues are resolved

## Frequency Recommendations

- **Weekly**: Check for updates, merge if significant changes
- **Before major work**: Always sync first
- **After upstream releases**: Sync immediately
- **When colleague mentions fixes**: Sync to get their changes

## Automation

### Weekly Sync Reminder

Add to your calendar or use a cron job:

```bash
# Add to crontab (runs every Monday at 9 AM)
0 9 * * 1 cd /Users/kirill/Documents/digital_brain/neuro-workflow && ./sync_with_upstream.sh
```

### Git Hooks (Advanced)

Create `.git/hooks/post-merge` to automatically test after merge:

```bash
#!/bin/bash
echo "Running post-merge tests..."
docker-compose -f gui/docker-compose.yml up -d
# Add your test commands
```

## Best Practices

1. **Always create backup branch** before merging
2. **Test immediately** after merge
3. **Document conflicts** - why you kept your version if you did
4. **Communicate with team** - let them know you've synced
5. **Keep commits clean** - one merge commit per sync
6. **Tag stable versions** - tag your branch after successful merges

## Summary

**Quick Reference**:
```bash
# 1. Save work
git add . && git commit -m "Your work"

# 2. Sync
./sync_with_upstream.sh
# OR manually: git fetch upstream && git merge upstream/main

# 3. Resolve conflicts (prefer upstream)
git checkout --theirs <conflicted-file>
git add <conflicted-file>
git commit

# 4. Test
docker-compose -f gui/docker-compose.yml up -d

# 5. Push to your repo
git push origin <your-branch>
```

**Time Required**: 10-30 minutes depending on conflicts

**Frequency**: Weekly or when upstream has important updates

