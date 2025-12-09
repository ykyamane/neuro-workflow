# Pushing to Upstream Repository (Admin Access)

Since you have admin rights to `oist/neuro-workflow`, you can push directly!

## Quick Push Command

```bash
# Push your branch to upstream repository
git push upstream feature/enhanced-version-20251203:feature/enhanced-version

# Or push with the same name
git push upstream feature/enhanced-version-20251203
```

## Authentication

You'll need to authenticate. Since you have admin rights, use your Personal Access Token:

1. **Create a PAT** (if you don't have one):
   - Go to: https://github.com/settings/tokens
   - Generate new token (classic)
   - Scopes: `repo` (full control)
   - Copy the token

2. **When prompted during push**:
   - Username: `kirillmitrofanov` (or your GitHub username)
   - Password: `<paste your PAT token>`

## Branch Naming Suggestions

Looking at existing branches on [oist/neuro-workflow/branches](https://github.com/oist/neuro-workflow/branches):
- `main` - default
- `dev_proxy` - development branch
- `mcp_dev` - MCP development

**Suggested names for your branch:**
- `feature/enhanced-version` - Clear and descriptive
- `feature/parameter-metadata-snakemake` - Feature-specific
- `enhanced-20251203` - Date-based
- `kirill/enhanced-version` - Namespace with your name

## Complete Push Process

```bash
# 1. Make sure you're on your branch
git checkout feature/enhanced-version-20251203

# 2. Push to upstream (will prompt for credentials)
git push upstream feature/enhanced-version-20251203:feature/enhanced-version

# 3. Verify on GitHub
# Go to: https://github.com/oist/neuro-workflow/branches
# Your branch should appear there!
```

## Store Credentials (Optional)

To avoid entering credentials every time:

```bash
# Configure Git credential helper (macOS)
git config --global credential.helper osxkeychain

# Now push (will ask once, then remember)
git push upstream feature/enhanced-version-20251203:feature/enhanced-version
```

## Alternative: Use SSH (More Secure)

If you prefer SSH:

```bash
# Change upstream to SSH
git remote set-url upstream git@github.com:oist/neuro-workflow.git

# Push (no password needed if SSH key is set up)
git push upstream feature/enhanced-version-20251203:feature/enhanced-version
```

## After Pushing

1. **Verify branch exists**: https://github.com/oist/neuro-workflow/branches
2. **Set as default branch** (if needed): GitHub Settings → Branches
3. **Protect branch** (if needed): GitHub Settings → Branches → Add rule
4. **Share with team**: Let them know the new branch is available

## Benefits of Direct Push (Admin Access)

- ✅ No PR needed - direct push
- ✅ Immediate availability
- ✅ Full control over branch
- ✅ Can set branch protection rules
- ✅ Can merge to main when ready

