# GitHub Bot Account Setup for Auto-Error Reporting

## Overview

Sugartalking includes automatic error reporting to GitHub Issues. To enable this feature with zero user configuration, you'll need to set up a GitHub bot account that reports errors to your repository.

## Why a Bot Account?

**Benefits**:
- ✅ Users don't need to configure anything
- ✅ All error reports go to one central location (your repo)
- ✅ You maintain control over the issue tracker
- ✅ Bot account can be limited to issue-creation only

**Alternative Approach** (not recommended for this project):
- Each user creates their own GitHub token
- Requires manual configuration
- Users won't do it → feature won't be used

## Step-by-Step Setup

### 1. Create a GitHub Bot Account

1. **Sign out** of your main GitHub account
2. Go to https://github.com/join
3. Create a new account:
   - **Username**: `sugartalking-bot` (or similar)
   - **Email**: Use a separate email (e.g., `sugartalking-bot@yourdomain.com`)
   - **Password**: Use a strong, unique password

4. **Verify the email** address

5. **(Optional)** Add a profile picture and bio:
   - Picture: Robot/bot icon
   - Bio: "Automated error reporting bot for Sugartalking project"

### 2. Grant Bot Access to Your Repository

1. Go to your repository: `https://github.com/builderOfTheWorlds/denon_avr_x2300w_webGUI`

2. Click **Settings** → **Collaborators and teams**

3. Click **Add people**

4. Add `sugartalking-bot` (or whatever username you chose)

5. Select permission level: **Write**
   - This allows creating issues but not pushing code

6. Bot account will receive an email invitation

7. **Accept the invitation** (while logged in as bot account)

### 3. Create a Personal Access Token (Classic)

1. **Log in as the bot account**

2. Go to **Settings** (click avatar → Settings)

3. Scroll down to **Developer settings** (left sidebar, bottom)

4. Click **Personal access tokens** → **Tokens (classic)**

5. Click **Generate new token** → **Generate new token (classic)**

6. Configure the token:
   - **Note**: "Sugartalking Error Reporting"
   - **Expiration**: **No expiration** (or set a reminder to renew)
   - **Scopes**: Select **ONLY**:
     - ✅ `public_repo` (for public repos)
     - OR ✅ `repo` (for private repos)

7. Click **Generate token**

8. **COPY THE TOKEN IMMEDIATELY** - you won't see it again!
   - It will look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 4. Store the Token Securely

#### Option A: Kubernetes Secret (Recommended)

```bash
# Base64 encode the token
echo -n 'ghp_your_token_here' | base64

# Create the secret
kubectl create secret generic sugartalking-secrets \
  --from-literal=GITHUB_TOKEN='ghp_your_token_here' \
  -n default

# Verify it was created
kubectl get secret sugartalking-secrets -n default
```

#### Option B: Update Secret Template

1. Copy the template:
   ```bash
   cp kubernetes/base/secret-template.yaml kubernetes/base/secret.yaml
   ```

2. Edit `kubernetes/base/secret.yaml`:
   ```yaml
   data:
     GITHUB_TOKEN: <base64-encoded-token>
   ```

3. Apply it:
   ```bash
   kubectl apply -f kubernetes/base/secret.yaml
   ```

#### Option C: Environment Variable (Local Testing)

```bash
# For docker-compose
export GITHUB_TOKEN=ghp_your_token_here
docker-compose -f docker/docker-compose.yml up
```

### 5. Update ConfigMap

Edit `kubernetes/base/configmap.yaml` to ensure it points to your repository:

```yaml
data:
  GITHUB_REPO: "builderOfTheWorlds/denon_avr_x2300w_webGUI"
```

### 6. Test the Setup

#### Deploy the Application

```bash
# Using installer
./kubernetes/installer.sh

# Or manually
kubectl apply -f kubernetes/base/
```

#### Trigger a Test Error

```bash
# Port forward to the app
kubectl port-forward svc/sugartalking 5000:80

# Trigger an error (visit a non-existent endpoint to force an error)
curl http://localhost:5000/api/trigger-test-error
```

#### Check if Issue Was Created

1. Go to your repository's Issues tab
2. Look for an issue titled `[Auto-Report] ...`
3. It should be labeled with `bug` and `auto-reported`

### 7. Security Best Practices

#### Rotate Tokens Regularly

Even with "no expiration", rotate tokens every 6-12 months:

1. Generate new token with same permissions
2. Update Kubernetes secret
3. Delete old token from GitHub settings
4. Restart pods to pick up new secret

```bash
# Update secret
kubectl create secret generic sugartalking-secrets \
  --from-literal=GITHUB_TOKEN='new_token_here' \
  -n default \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment to pick up new secret
kubectl rollout restart deployment/sugartalking -n default
```

#### Limit Token Scope

- **DO**: Use `public_repo` scope for public repositories
- **DO**: Use `repo` scope ONLY if repository is private
- **DON'T**: Add `admin` or `delete` scopes
- **DON'T**: Give bot account admin access to repository

#### Monitor Bot Activity

Periodically check what the bot is doing:

```bash
# View issues created by bot
https://github.com/builderOfTheWorlds/denon_avr_x2300w_webGUI/issues?q=is%3Aissue+author%3Asugartalking-bot
```

### 8. Disable Auto-Reporting (If Needed)

#### Globally

Update ConfigMap:
```yaml
data:
  AUTO_REPORT_ERRORS: "false"
```

Then restart:
```bash
kubectl rollout restart deployment/sugartalking -n default
```

#### Per-User Installation

Users can override in their deployment:
```bash
kubectl set env deployment/sugartalking AUTO_REPORT_ERRORS=false -n default
```

## Troubleshooting

### Issue Not Created

**Check 1: Token Valid?**
```bash
# Test token manually
curl -H "Authorization: token ghp_your_token" \
  https://api.github.com/user

# Should return bot account info
```

**Check 2: Bot Has Write Access?**
- Go to repo Settings → Collaborators
- Verify bot is listed with Write permission

**Check 3: Token Has Correct Scope?**
- Go to bot account Settings → Developer settings → Personal access tokens
- Verify `repo` or `public_repo` is checked

**Check 4: Check App Logs**
```bash
kubectl logs -l app=sugartalking -n default | grep -i github
```

### Too Many Issues Being Created

**Problem**: Errors are creating duplicate issues

**Solution**: The system already checks for duplicates. If you're seeing duplicates:

1. Check `app/services/error_reporter.py` - `_find_existing_issue()` function
2. Increase the similarity threshold
3. Or rate-limit issue creation:

```python
# Add to error_reporter.py
ISSUE_CREATION_COOLDOWN = 300  # 5 minutes

def _can_create_issue(self):
    last_issue_time = self.get_last_issue_time()
    if time.time() - last_issue_time < ISSUE_CREATION_COOLDOWN:
        return False
    return True
```

### Token Expired

If you set an expiration and forgot to renew:

1. Generate a new token (same steps as above)
2. Update the Kubernetes secret
3. Restart deployment

### Want to Switch to User Tokens Instead

Edit `kubernetes/base/secret-template.yaml` instructions to guide users to create their own tokens, then:

1. Remove bot account from collaborators
2. Delete bot account token
3. Update documentation to require user configuration

## Alternative: GitHub App (Advanced)

For a more enterprise solution, create a GitHub App instead of using a bot account:

### Benefits
- More granular permissions
- Better audit trail
- No password to manage
- Can be installed on multiple repos

### Drawbacks
- More complex setup
- Requires webhook endpoint
- Overkill for this project

**Not recommended for homelab use**, but if you want to explore:
- https://docs.github.com/en/apps/creating-github-apps

## FAQ

**Q: Can I use my personal account instead of a bot?**
A: Yes, but not recommended. Your personal token has access to all your repos, which is a security risk.

**Q: What if my repository is private?**
A: Use the `repo` scope instead of `public_repo` when creating the token.

**Q: Can users opt out of error reporting?**
A: Yes, they can set `AUTO_REPORT_ERRORS=false` in their deployment.

**Q: Will this expose user data?**
A: The error reporter sanitizes IP addresses and file paths before reporting. Review `app/services/error_reporter.py` to verify.

**Q: How much will this cost?**
A: Free! GitHub Actions has generous limits, and creating issues is not rate-limited for normal use.

**Q: Can I use this for my fork?**
A: Yes! Just create your own bot account and point `GITHUB_REPO` to your fork.

## Summary Checklist

- [ ] Create bot account `sugartalking-bot`
- [ ] Add bot to repository with Write permission
- [ ] Generate personal access token with `repo` scope
- [ ] Store token in Kubernetes secret
- [ ] Update `GITHUB_REPO` in ConfigMap
- [ ] Deploy application
- [ ] Test error reporting
- [ ] Set token rotation reminder (6-12 months)

---

**Last Updated**: 2025-11-08
**Bot Account**: `sugartalking-bot` (replace with your actual bot username)
**Repository**: `builderOfTheWorlds/denon_avr_x2300w_webGUI`
