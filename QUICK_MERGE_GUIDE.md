# Quick Merge Guide - TL;DR

## Current Situation
- **19 commits** behind upstream
- **4 files** with conflict risk (you modified, upstream also modified)
- **60+ files** changed in upstream

## Quick Start (Recommended Approach)

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow

# 1. Save your work
git add .
git commit -m "Local enhancements before merge"

# 2. Backup
git branch backup-$(date +%Y%m%d)

# 3. Merge upstream
git merge origin/main

# 4. Resolve conflicts (4 files):
#    - gui/docker-compose.yml
#    - gui/workflow_backend/.../jupyterhub_config.py
#    - gui/workflow_frontend/src/auth/supabase.ts
#    - gui/workflow_frontend/src/protectedRoute.tsx

# 5. Test
docker-compose -f gui/docker-compose.yml up -d

# 6. Create feature branch
git checkout -b feature/enhancements-$(date +%Y%m%d)
```

## Conflict Resolution Strategy

For each of the 4 conflicted files:
1. Open in VS Code (shows three-way merge view)
2. Compare your changes vs upstream changes
3. Keep both fixes if they address different issues
4. Test after resolving each file

## If Something Goes Wrong

```bash
# Undo merge
git merge --abort

# Or restore from backup
git checkout backup-$(date +%Y%m%d)
```

## See What Changed

```bash
./compare_upstream.sh  # Shows detailed comparison
```

## Full Details

See `MERGE_STRATEGY.md` for complete guide.

