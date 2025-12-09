# GitHub Authentication Setup

## Issue
GitHub no longer accepts password authentication for Git operations. You need to use a Personal Access Token (PAT) or SSH keys.

## Solution: Use Personal Access Token (PAT)

### Step 1: Create a Personal Access Token on GitHub

1. Go to GitHub.com and log in
2. Click your profile picture (top right) → **Settings**
3. Scroll down to **Developer settings** (left sidebar, at the bottom)
4. Click **Personal access tokens** → **Tokens (classic)**
5. Click **Generate new token** → **Generate new token (classic)**
6. Give it a name: `NeuroWorkflow Development`
7. Set expiration (recommend 90 days or custom)
8. Select scopes (permissions):
   - ✅ **repo** (Full control of private repositories)
     - This includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
9. Click **Generate token**
10. **IMPORTANT**: Copy the token immediately - you won't be able to see it again!
   - It will look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Use the Token for Authentication

**Option A: Use Token as Password (Recommended for first time)**

When Git asks for password, paste your token instead:

```bash
git push -u origin feature/enhanced-version-20251203
# Username: kirillmitrofanov
# Password: <paste your token here>
```

**Option B: Store Credentials (More Convenient)**

Store your credentials so you don't have to enter them every time:

```bash
# Store credentials in Git credential helper
git config --global credential.helper osxkeychain  # For macOS

# Then push (will prompt once, then remember)
git push -u origin feature/enhanced-version-20251203
# Username: kirillmitrofanov
# Password: <paste your token>
```

**Option C: Include Token in Remote URL (Less Secure)**

You can embed the token in the URL (not recommended for shared machines):

```bash
git remote set-url origin https://kirillmitrofanov:YOUR_TOKEN@github.com/kirillmitrofanov/neuro-workflow.git
git push -u origin feature/enhanced-version-20251203
```

## Alternative: Use SSH Authentication (More Secure)

### Step 1: Generate SSH Key (if you don't have one)

```bash
# Check if you already have SSH keys
ls -la ~/.ssh

# If no keys exist, generate one
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept default location
# Enter a passphrase (optional but recommended)
```

### Step 2: Add SSH Key to GitHub

```bash
# Copy your public key
cat ~/.ssh/id_ed25519.pub
# Copy the entire output
```

Then on GitHub:
1. Go to **Settings** → **SSH and GPG keys**
2. Click **New SSH key**
3. Title: `MacBook Air - NeuroWorkflow`
4. Paste your public key
5. Click **Add SSH key**

### Step 3: Change Remote to SSH

```bash
# Change remote URL to SSH
git remote set-url origin git@github.com:kirillmitrofanov/neuro-workflow.git

# Verify
git remote -v

# Test connection
ssh -T git@github.com
# Should say: "Hi kirillmitrofanov! You've successfully authenticated..."

# Now push (no password needed!)
git push -u origin feature/enhanced-version-20251203
```

## Quick Fix (Use PAT Now)

For immediate push, use a Personal Access Token:

1. **Create token** (see Step 1 above)
2. **Push with token**:
   ```bash
   git push -u origin feature/enhanced-version-20251203
   # When prompted:
   # Username: kirillmitrofanov
   # Password: <paste your PAT token here>
   ```

## Security Notes

- **Never commit tokens to Git** - they will be in history
- **Use SSH for long-term** - more secure and convenient
- **Rotate tokens regularly** - especially if shared
- **Use fine-grained tokens** if possible (newer GitHub feature)

## Troubleshooting

### "Permission denied" error
- Check token has `repo` scope
- Verify token hasn't expired
- Make sure repository exists and you have write access

### "Repository not found" error
- Verify repository exists at: https://github.com/kirillmitrofanov/neuro-workflow
- Check you have write permissions
- Try creating the repository on GitHub first if it doesn't exist

### Token not working
- Regenerate token
- Check token hasn't expired
- Verify scopes are correct

