# 📤 GitHub Upload Guide for Petrol Pump V2

This guide will walk you through uploading your Petrol Pump V2 application to GitHub.

---

## 🎯 Prerequisites

Before you begin, make sure you have:
- [x] A GitHub account ([Create one here](https://github.com/signup))
- [x] Git installed on your system
- [x] Access to your project directory

---

## 📋 Step-by-Step Instructions

### Step 1: Create a New Repository on GitHub

1. **Go to GitHub** and sign in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Fill in the details:
   ```
   Repository name: petrol_pump_v2
   Description: Comprehensive Petrol Pump Management System for ERPNext
   Visibility: ☑ Public (or Private if you prefer)
   
   ☐ Add a README file (we already have one)
   ☐ Add .gitignore (we already have one)
   ☐ Choose a license (we already have MIT License)
   ```
4. Click **"Create repository"**

You'll be redirected to your new repository page. Keep it open!

---

### Step 2: Initialize Git in Your Project (If Not Already Done)

Open your terminal and navigate to the app directory:

```bash
# Navigate to your app directory
cd /home/super/dev/erp-bench/apps/petrol_pump_v2

# Check if git is already initialized
git status

# If you get "fatal: not a git repository", initialize it:
git init

# Set your identity (if not set globally)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

---

### Step 3: Add All Files to Git

```bash
# Add all files
git add .

# Check what's being added
git status

# You should see all your files in green
```

---

### Step 4: Create Initial Commit

```bash
# Create your first commit
git commit -m "Initial commit: Petrol Pump Management System V2

- Complete petrol pump management system for ERPNext
- Features: Day Closing, Shift Reading, Dip Reading, Fuel Testing, Fuel Transfer
- Integrated with ERPNext Stock, Accounts, and Sales modules
- Automatic Stock Entry, Sales Invoice, and Payment Entry creation
- Multi-pump support with role-based permissions
- Real-time inventory tracking and reconciliation
- Comprehensive documentation included"
```

---

### Step 5: Add Remote Repository

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
# Add GitHub as remote origin
git remote add origin https://github.com/YOUR_USERNAME/petrol_pump_v2.git

# Verify remote was added
git remote -v
```

---

### Step 6: Push to GitHub

```bash
# Push to GitHub (first time)
git branch -M main
git push -u origin main
```

**If prompted for credentials:**
- Username: Your GitHub username
- Password: Use a **Personal Access Token** (not your GitHub password!)

#### How to Create a Personal Access Token:

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "ERPNext Petrol Pump App"
4. Select scopes: ✓ `repo` (all)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)
7. Use this token as your password when pushing

---

### Step 7: Verify Upload

1. Go to your GitHub repository page: `https://github.com/YOUR_USERNAME/petrol_pump_v2`
2. You should see all your files!
3. Check that README.md is displaying properly
4. Verify FLOW.md and other docs are there

---

## 🔄 Making Future Updates

When you make changes to your code:

```bash
# Check what changed
git status

# Add changed files
git add .

# Or add specific files
git add path/to/specific/file.py

# Commit with a meaningful message
git commit -m "Fix: Resolved exchange rate error in Day Closing"

# Push to GitHub
git push origin main
```

---

## 📝 Commit Message Best Practices

Use these prefixes for clear commit history:

```
feat: Add new feature
fix: Bug fix
docs: Documentation changes
style: Code formatting (no logic change)
refactor: Code restructuring (no logic change)
test: Adding tests
chore: Maintenance tasks

Examples:
- feat: Add cash variance approval workflow
- fix: Resolve naming series counter issue
- docs: Update FLOW.md with testing scenario
- refactor: Improve Day Closing validation logic
```

---

## 🏷️ Creating Releases (Optional)

To create version releases:

```bash
# Tag a release
git tag -a v2.0.0 -m "Version 2.0.0 - Initial stable release"

# Push tags
git push origin --tags
```

Then go to GitHub → Releases → Create a new release

---

## 🌿 Branching Strategy (Recommended)

For organized development:

```bash
# Create a development branch
git checkout -b develop

# Make changes and commit
git add .
git commit -m "feat: Add new feature"

# Push development branch
git push origin develop

# When ready to merge to main:
git checkout main
git merge develop
git push origin main
```

**Suggested Branches:**
- `main` - Stable production code
- `develop` - Development work
- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes

---

## 🔧 Troubleshooting

### Error: "Permission denied (publickey)"

**Solution: Use HTTPS instead of SSH**
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/petrol_pump_v2.git
```

### Error: "failed to push some refs"

**Solution: Pull first, then push**
```bash
git pull origin main --rebase
git push origin main
```

### Error: "fatal: refusing to merge unrelated histories"

**Solution: Force the merge**
```bash
git pull origin main --allow-unrelated-histories
```

### Large files not uploading

**Solution: Use Git LFS for files > 50MB**
```bash
git lfs install
git lfs track "*.large_file_extension"
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

---

## 📦 Exclude Sensitive Files

Make sure your `.gitignore` is working:

```bash
# Test if files are ignored
git status

# If sensitive files appear (like site_config.json), add to .gitignore:
echo "site_config.json" >> .gitignore
git add .gitignore
git commit -m "chore: Ignore sensitive config files"
```

**Files to NEVER commit:**
- `site_config.json` (contains database passwords)
- `.env` files (environment variables)
- Database backups (`.sql` files)
- Private files/directories
- API keys or tokens

---

## 🎨 Customize Your README

Before pushing, update these in `README.md`:

1. **Replace placeholders:**
   - `YOUR_USERNAME` → Your GitHub username
   - `your.email@example.com` → Your email
   - `Your Name` → Your name

2. **Add badges** (optional):
   ```markdown
   ![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/petrol_pump_v2)
   ![GitHub forks](https://img.shields.io/github/forks/YOUR_USERNAME/petrol_pump_v2)
   ![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/petrol_pump_v2)
   ```

3. **Add screenshots** (optional):
   ```markdown
   ## Screenshots
   
   ![Day Closing](screenshots/day_closing.png)
   ![Dashboard](screenshots/dashboard.png)
   ```

---

## 📸 Adding Screenshots (Optional)

To make your repository more attractive:

1. **Create screenshots directory:**
   ```bash
   mkdir screenshots
   ```

2. **Take screenshots** of:
   - Day Closing form
   - Dispenser list
   - Fuel Tank view
   - Reports/Dashboard

3. **Add images:**
   ```bash
   git add screenshots/
   git commit -m "docs: Add application screenshots"
   git push
   ```

4. **Reference in README:**
   ```markdown
   ![Day Closing Screenshot](screenshots/day_closing.png)
   ```

---

## 🔗 Setting Up GitHub Pages (Optional)

To host documentation:

1. Go to repository **Settings** → **Pages**
2. Source: `main` branch → `/docs` folder (or root)
3. Save
4. Your docs will be at: `https://YOUR_USERNAME.github.io/petrol_pump_v2/`

---

## 👥 Collaborating

To allow others to contribute:

1. **Add collaborators:**
   - Settings → Collaborators → Add people

2. **Accept pull requests:**
   - Review → Approve → Merge

3. **Create issues:**
   - Issues tab → New issue
   - Use labels: bug, enhancement, documentation, etc.

---

## 🎉 After Upload Checklist

- [ ] Repository is public (or private as intended)
- [ ] README displays correctly
- [ ] All important files uploaded
- [ ] No sensitive data committed
- [ ] .gitignore working properly
- [ ] License file included
- [ ] Documentation (FLOW.md) accessible
- [ ] Repository description added
- [ ] Topics/tags added (erpnext, petrol-pump, python, frappe)

---

## 📞 Need Help?

- GitHub Docs: https://docs.github.com/
- Git Docs: https://git-scm.com/doc
- Frappe Community: https://discuss.frappe.io/

---

## 🎓 Quick Reference Commands

```bash
# Daily workflow
git status                    # Check what changed
git add .                     # Stage all changes
git commit -m "message"       # Commit with message
git push                      # Push to GitHub

# Branching
git branch                    # List branches
git checkout -b feature-name  # Create new branch
git checkout main             # Switch to main
git merge feature-name        # Merge branch

# Sync with remote
git pull                      # Pull latest changes
git fetch                     # Fetch without merging
git remote -v                 # Show remotes

# Undo changes
git reset HEAD file.py        # Unstage file
git checkout -- file.py       # Discard local changes
git revert <commit-hash>      # Revert a commit

# View history
git log                       # Commit history
git log --oneline             # Compact history
git diff                      # Show changes
```

---

**Happy Coding! 🚀**

Once uploaded, share your repository URL with the community and let others benefit from your work!

