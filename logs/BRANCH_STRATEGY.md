# Branch Strategy for Upstream Repository

## Goal
Create your enhanced version as a new branch on the upstream repository: https://github.com/oist/neuro-workflow

## Two Approaches

### Option 1: Direct Push (If You Have Write Access)

If you're a collaborator on the `oist/neuro-workflow` repository, you can push directly:

```bash
# Push your branch to upstream
git push upstream feature/enhanced-version-20251203

# Or with a different name
git push upstream feature/enhanced-version-20251203:feature/enhanced-version
```

**Check if you have access:**
- Try pushing: `git push upstream feature/enhanced-version-20251203`
- If it works, you have write access!
- If you get "permission denied", you need to use Option 2

### Option 2: Pull Request Workflow (Standard Approach)

If you don't have direct write access (most common), use this workflow:

#### Step 1: Push to Your Fork

```bash
# Push to your fork (origin)
git push -u origin feature/enhanced-version-20251203
```

#### Step 2: Create Pull Request on GitHub

1. Go to: https://github.com/oist/neuro-workflow
2. Click **"Pull requests"** tab
3. Click **"New pull request"**
4. Click **"compare across forks"**
5. Set:
   - **base repository**: `oist/neuro-workflow`
   - **base branch**: `main` (or the branch you want to merge into)
   - **head repository**: `kirillmitrofanov/neuro-workflow`
   - **compare branch**: `feature/enhanced-version-20251203`
6. Click **"Create pull request"**
7. Fill in:
   - **Title**: "Enhanced version: Parameter metadata, SnakeMake, job managers"
   - **Description**: Explain your enhancements
8. Click **"Create pull request"**

#### Step 3: Repository Maintainers Review

- The maintainers will review your PR
- They may request changes
- Once approved, they can:
  - Merge into `main` (most common)
  - Create a new branch from your PR
  - Request you create a branch directly (if they give you access)

## Recommended Branch Naming

Looking at the existing branches on [oist/neuro-workflow/branches](https://github.com/oist/neuro-workflow/branches):
- `main` - default branch
- `dev_proxy` - development branch
- `mcp_dev` - MCP development branch

**Suggested names for your branch:**
- `feature/enhanced-version` - Clear and descriptive
- `feature/parameter-metadata-snakemake` - Feature-specific
- `enhanced-20251203` - Date-based
- `kirill/enhanced-version` - Namespace with your name

## Current Setup

Your current remotes:
- `origin` → `kirillmitrofanov/neuro-workflow` (your fork)
- `upstream` → `oist/neuro-workflow` (original repository)

## Workflow Summary

### If You Have Write Access to Upstream:

```bash
# Push directly to upstream
git push upstream feature/enhanced-version-20251203:feature/enhanced-version

# Verify on GitHub
# Go to: https://github.com/oist/neuro-workflow/branches
```

### If You Don't Have Write Access (Standard):

```bash
# 1. Push to your fork
git push -u origin feature/enhanced-version-20251203

# 2. Create PR on GitHub (via web interface)
# 3. Wait for maintainer review/approval
# 4. Maintainer merges or creates branch
```

## Testing Write Access

Try this command to test:

```bash
git push upstream feature/enhanced-version-20251203:test-branch-access 2>&1
```

**If successful**: You have write access! You can push your branch.

**If you get "permission denied"**: Use the Pull Request workflow.

## Best Practice Recommendation

Even if you have write access, consider:

1. **Create PR first** - Allows for code review and discussion
2. **Get feedback** - Team can review before merging
3. **Document changes** - PR description explains what you added
4. **Maintain history** - PR shows the evolution of changes

Then, if the team wants it as a permanent branch, they can create it from your PR.

## Next Steps

1. **Test access**: Try `git push upstream feature/enhanced-version-20251203`
2. **If it works**: Great! Your branch will appear on the branches page
3. **If it doesn't**: Push to your fork and create a PR

