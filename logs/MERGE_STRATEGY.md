# Upstream Merge Strategy

## Current Situation

**Your Local State**:
- Branch: `main`
- Last synced commit: `69b30df` ("Addressing remaining issues")
- Status: 13 modified files + many new untracked files

**Upstream Repository** (https://github.com/oist/neuro-workflow):
- Latest commit: `146ee7b` ("feat(jupyterhub): allow embedding")
- **16 new commits** since your last sync

**Upstream Changes Include**:
- JupyterHub embedding support
- Docker improvements (TVB libraries, Miniconda, MRtrix3)
- Bug fixes (node instance names, file names, Jupyter display issues)
- Workflow execution support
- Node color settings
- Supabase credential templates
- JupyterLab URL fixes
- Chatbot view fixes

## Recommended Approach

Your idea of creating a separate folder is reasonable, but since you already have a Git repository, we can use Git's built-in merge capabilities which are more reliable and maintain history.

### Option 1: Git-Based Merge (Recommended)

**Advantages**:
- Preserves full history
- Automatic conflict detection
- Easy to track what changed
- Can undo if needed
- Standard Git workflow

**Steps**:

1. **Save your current work**
   ```bash
   # Commit your changes (or stash them)
   git add .
   git commit -m "Local changes: parameter metadata, SnakeMake, job managers, documentation"
   ```

2. **Create a backup branch** (safety net)
   ```bash
   git branch backup-before-merge-$(date +%Y%m%d)
   ```

3. **Fetch and examine upstream changes**
   ```bash
   git fetch origin
   git log HEAD..origin/main --oneline  # See what's new
   git diff HEAD..origin/main --stat     # See which files changed
   ```

4. **Merge upstream changes**
   ```bash
   git merge origin/main
   ```

5. **Resolve conflicts** (if any)
   - Git will mark conflicted files
   - Review each conflict
   - Choose your version, upstream version, or combine both

6. **Test the merged code**
   - Run your test suite
   - Verify Docker setup
   - Check GUI functionality

7. **Create your feature branch**
   ```bash
   git checkout -b feature/your-enhancements
   git push origin feature/your-enhancements
   ```

### Option 2: Manual Comparison (Your Original Idea)

If you prefer a more controlled, manual approach:

**Steps**:

1. **Create comparison directory**
   ```bash
   cd /Users/kirill/Documents/digital_brain
   mkdir neuro-workflow-upstream-$(date +%Y%m%d)
   cd neuro-workflow-upstream-$(date +%Y%m%d)
   git clone https://github.com/oist/neuro-workflow.git .
   ```

2. **Compare with your version**
   ```bash
   # Use diff tools to compare
   diff -r ../neuro-workflow/src ./src
   # Or use a visual diff tool like:
   # - VS Code's built-in diff
   # - Meld
   # - Beyond Compare
   ```

3. **Document differences**
   - Create a list of files that changed
   - Note which changes are compatible
   - Identify potential conflicts

4. **Selective merge**
   - Manually copy upstream changes you want
   - Keep your enhancements
   - Test thoroughly

**Advantages**:
- Full control over what gets merged
- Can review every change before applying
- No risk of automatic merge mistakes

**Disadvantages**:
- More time-consuming
- Easy to miss changes
- No automatic conflict resolution
- Harder to track what was merged

## Detailed Comparison Results

### Files Changed in Upstream (19 commits, 60+ files)

**New Files Added**:
- `data/bmcr_data/atlas_segmentation_BM1.nii.gz` - BMCR atlas data
- `data/tvb_data/connectivity_76.zip` - TVB connectivity data
- `examples/epilepsy_rs_bmcr.py` - New epilepsy example
- `gui/uninstall.sh` - Uninstall script
- `gui/workflow_backend/django-project/app/workflow/run_workflow_service.py` - Workflow execution service
- `gui/workflow_frontend/src/views/home/components/chatbotView.tsx` - Chatbot view (you also created this!)
- `gui/workflow_frontend/src/views/home/components/logViewModal.tsx` - Log viewing modal
- `src/neuroworkflow/nodes/io/BMCR_Conn_To_TVB.py` - BMCR to TVB connector node
- `src/neuroworkflow/nodes/io/BMCR_DTI_to_Connectome.py` - DTI to connectome node

**Modified Files** (key ones):
- `gui/docker-compose.yml` - Docker configuration (YOU MODIFIED THIS TOO)
- `gui/workflow_backend/Dockerfile` - Backend Docker image
- `gui/workflow_backend/Dockerfile.jupyter` - Jupyter Docker image
- `gui/workflow_backend/django-project/neuroworkflow/jupyterhub_config.py` - JupyterHub config (YOU MODIFIED THIS TOO)
- `gui/workflow_frontend/src/auth/supabase.ts` - Supabase client (YOU MODIFIED THIS TOO)
- `gui/workflow_frontend/src/protectedRoute.tsx` - Route protection (YOU MODIFIED THIS TOO)
- Multiple backend services (box, workflow, auth)
- Multiple frontend components (home, box, file views)

### Conflict Risk Assessment

**HIGH CONFLICT RISK** (4 files you modified that also changed upstream):
1. `gui/docker-compose.yml` - Both modified Docker setup
2. `gui/workflow_backend/django-project/neuroworkflow/jupyterhub_config.py` - Both fixed JupyterHub issues
3. `gui/workflow_frontend/src/auth/supabase.ts` - Both fixed Supabase configuration
4. `gui/workflow_frontend/src/protectedRoute.tsx` - Both added dev mode bypass

**LOW CONFLICT RISK** (upstream changed, you didn't):
- Most backend services
- Most frontend components
- New example files
- New nodes

**NO CONFLICT** (you added, upstream didn't):
- All your new documentation files
- Parameter metadata service
- SnakeMake generator
- Job managers
- Test notebooks

## Recommended Merge Strategy

### Step-by-Step Plan

#### Phase 1: Preparation (5 minutes)

```bash
cd /Users/kirill/Documents/digital_brain/neuro-workflow

# 1. Commit your current work
git add .
git commit -m "WIP: Local enhancements - parameter metadata, SnakeMake, job managers, documentation"

# 2. Create safety backup
git branch backup-before-merge-$(date +%Y%m%d)

# 3. Verify you're on main branch
git checkout main
```

#### Phase 2: Examine Conflicts (10 minutes)

```bash
# See what conflicts you'll have
git merge --no-commit --no-ff origin/main

# If conflicts occur, examine them:
git status  # Shows conflicted files
```

For each conflicted file, you'll need to decide:
- **Keep your version** (if your fix is better)
- **Keep upstream version** (if their fix is better)
- **Combine both** (if fixes address different issues)

#### Phase 3: Resolve Conflicts (30-60 minutes)

**For `gui/docker-compose.yml`**:
- Your changes: Added volume mount for frontend source
- Upstream changes: Likely network configuration, TVB libraries
- **Action**: Combine both - keep your volume mount + their network/TVB changes

**For `jupyterhub_config.py`**:
- Your changes: Fixed network name, removed allowed_users restriction
- Upstream changes: Likely similar fixes + embedding support
- **Action**: Compare line-by-line, likely combine both fixes

**For `supabase.ts`**:
- Your changes: Added validation and mock client for dev mode
- Upstream changes: Likely similar fixes
- **Action**: Compare implementations, keep the better one or combine

**For `protectedRoute.tsx`**:
- Your changes: Added dev mode bypass
- Upstream changes: Likely similar or related fixes
- **Action**: Compare, likely combine

#### Phase 4: Complete Merge (5 minutes)

```bash
# After resolving conflicts:
git add <resolved-files>
git commit -m "Merge upstream changes from oist/neuro-workflow

- Integrated workflow execution support
- Added TVB libraries and Miniconda to Docker images
- Fixed JupyterHub embedding and CORS issues
- Added new BMCR and TVB nodes
- Resolved conflicts in docker-compose, jupyterhub_config, supabase, protectedRoute"
```

#### Phase 5: Test (30 minutes)

```bash
# Test critical functionality
docker-compose -f gui/docker-compose.yml up -d
# Check that services start correctly
# Test GUI access
# Test JupyterHub login
# Test workflow execution
```

#### Phase 6: Create Feature Branch (5 minutes)

```bash
# Create a branch for your enhancements
git checkout -b feature/enhancements-$(date +%Y%m%d)

# Push to your fork (if you have one) or create one
# git remote add myfork <your-fork-url>
# git push myfork feature/enhancements-$(date +%Y%m%d)
```

## Alternative: Three-Way Comparison Approach

If you want maximum control, use this hybrid approach:

### Step 1: Create Upstream Snapshot

```bash
cd /Users/kirill/Documents/digital_brain
mkdir neuro-workflow-upstream-20251127
cd neuro-workflow-upstream-20251127
git clone https://github.com/oist/neuro-workflow.git .
git checkout 146ee7b  # Latest upstream commit
```

### Step 2: Use Visual Diff Tool

Open three-way comparison:
- **Left**: Your current code (`/Users/kirill/Documents/digital_brain/neuro-workflow`)
- **Middle**: Base version (commit `69b30df` - where you started)
- **Right**: Latest upstream (`neuro-workflow-upstream-20251127`)

Tools:
- **VS Code**: Built-in three-way merge view
- **Meld**: Free, excellent for three-way diffs
- **Beyond Compare**: Commercial, very powerful

### Step 3: Selective Merge

For each conflicted file:
1. See what changed in upstream
2. See what you changed
3. Manually combine the best parts
4. Test each file

## Conflict Resolution Guide

### File-by-File Strategy

#### `gui/docker-compose.yml`

**Your changes** (likely):
- Added `volumes: - ./workflow_frontend/src:/frontend/src`

**Upstream changes** (likely):
- Network configuration
- TVB service additions
- JupyterHub network fixes

**Resolution**: Keep both. Your volume mount is important for development, their network fixes are important for functionality.

#### `jupyterhub_config.py`

**Your changes**:
- Fixed `network_name` from `"jupyterhub-network"` to `"neuro-workflow_workflow"`
- Commented out `allowed_users` restriction

**Upstream changes** (likely):
- Similar network fixes
- Embedding support
- CORS configuration

**Resolution**: Compare line-by-line. Both likely fixed the same issues, but upstream may have additional features.

#### `supabase.ts`

**Your changes**:
- Added URL validation
- Created mock client for dev mode
- Better error handling

**Upstream changes** (likely):
- Similar validation
- Template updates

**Resolution**: Your implementation looks more robust. Keep yours, but check if upstream added any new features.

#### `protectedRoute.tsx`

**Your changes**:
- Added dev mode bypass when Supabase not configured

**Upstream changes** (likely):
- Similar dev mode handling

**Resolution**: Compare implementations, keep the more complete one.

## Testing Checklist

After merging, test:

- [ ] Docker services start: `docker-compose up -d`
- [ ] Frontend loads: `http://localhost:5173`
- [ ] Backend API works: `http://localhost:3000/api`
- [ ] JupyterHub login works
- [ ] JupyterHub spawns containers
- [ ] Workflow execution works
- [ ] Node upload works
- [ ] Parameter metadata service (your addition) works
- [ ] SnakeMake generation (your addition) works
- [ ] SLURM job manager (your addition) works

## Rollback Plan

If something goes wrong:

```bash
# Option 1: Undo the merge
git merge --abort  # If merge in progress
git reset --hard backup-before-merge-20251127  # If merge completed

# Option 2: Revert specific files
git checkout backup-before-merge-20251127 -- <file-path>

# Option 3: Start fresh from backup branch
git checkout backup-before-merge-20251127
git checkout -b recovery-$(date +%Y%m%d)
```

## Next Steps After Successful Merge

1. **Test thoroughly** - Run all your test notebooks
2. **Document conflicts resolved** - Update this file with what you did
3. **Create pull request** - If you have a fork, create PR to upstream
4. **Coordinate with colleague** - Share what you merged and any issues
5. **Update documentation** - If merge changes how things work

## Questions to Ask Your Colleague

Before merging, you might want to ask:

1. "What specific issues did you fix in docker-compose.yml?"
2. "Did you also fix the JupyterHub network issue?"
3. "What's the new workflow execution service about?"
4. "Are there any breaking changes I should know about?"
5. "Should I test anything specific after merging?"

## Summary

**Your approach is sound**, but I recommend:

1. **Use Git merge** (Option 1) rather than manual copying - it's safer and preserves history
2. **Create backup branch first** - safety net
3. **Resolve 4 conflicts carefully** - these are the files you both modified
4. **Test thoroughly** - especially Docker and JupyterHub
5. **Create feature branch** - for your enhancements

The comparison script (`compare_upstream.sh`) will help you see exactly what changed. Run it anytime to check for new upstream updates.

**Estimated Time**: 1-2 hours for careful merge and testing
**Risk Level**: Low (you have backups and can rollback)
**Recommendation**: Proceed with Git merge approach

