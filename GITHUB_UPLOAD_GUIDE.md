# 📤 GitHub Upload Guide

## Step-by-Step Instructions to Upload Your Project to GitHub

### Prerequisites
- Git installed on your computer
- GitHub account created
- Repository created on GitHub

---

## Method 1: Using Git Command Line (Recommended)

### Step 1: Initialize Git Repository

Open terminal/command prompt in your project folder:

```bash
cd C:\PROJECTS\Oudience_Experiment
git init
```

### Step 2: Add All Files

```bash
git add .
```

This will stage all files except those in `.gitignore`

### Step 3: Create Initial Commit

```bash
git commit -m "Initial commit: Oudience AI Assistant v1.0"
```

### Step 4: Connect to GitHub Repository

Replace `yourusername` and `your-repo-name` with your actual GitHub username and repository name:

```bash
git remote add origin https://github.com/yourusername/your-repo-name.git
```

### Step 5: Push to GitHub

```bash
git branch -M main
git push -u origin main
```

If prompted, enter your GitHub credentials.

---

## Method 2: Using GitHub Desktop (Easier)

### Step 1: Download GitHub Desktop
- Download from: https://desktop.github.com/
- Install and sign in with your GitHub account

### Step 2: Add Your Repository
1. Click "File" → "Add Local Repository"
2. Browse to `C:\PROJECTS\Oudience_Experiment`
3. Click "Add Repository"

### Step 3: Create Initial Commit
1. You'll see all changed files
2. Add commit message: "Initial commit: Oudience AI Assistant v1.0"
3. Click "Commit to main"

### Step 4: Publish to GitHub
1. Click "Publish repository"
2. Choose repository name
3. Add description (optional)
4. Choose public or private
5. Click "Publish Repository"

---

## Method 3: Using VS Code (If you use VS Code)

### Step 1: Open Project in VS Code
```bash
code C:\PROJECTS\Oudience_Experiment
```

### Step 2: Initialize Repository
1. Click Source Control icon (left sidebar)
2. Click "Initialize Repository"

### Step 3: Stage and Commit
1. Click "+" next to "Changes" to stage all files
2. Enter commit message: "Initial commit: Oudience AI Assistant v1.0"
3. Click ✓ (checkmark) to commit

### Step 4: Push to GitHub
1. Click "..." menu in Source Control
2. Select "Remote" → "Add Remote"
3. Enter your GitHub repository URL
4. Click "Publish Branch"

---

## Important: Before Uploading

### 1. Check .gitignore
Make sure these are in `.gitignore`:
```
.venv/
venv/
flask_sessions/
*.db
uploads_exp/*.pdf
knowledge_base_exp.json
upload_logs.json
```

### 2. Remove Sensitive Data

**Change admin token in app.py:**
```python
# Before uploading, change this:
ADMIN_TOKEN = "admin123"  # ❌ Don't upload this!

# To this:
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'change-me-in-production')  # ✅ Better
```

### 3. Create Example Files

Already created for you:
- `knowledge_base_exp.json.example`
- `upload_logs.json.example`

### 4. Verify Files to Upload

Check what will be uploaded:
```bash
git status
```

Should NOT include:
- `.venv/` folder
- `flask_sessions/` folder
- PDF files in `uploads_exp/`
- `analytics.db`
- Actual `knowledge_base_exp.json` (use .example instead)

---

## After Uploading

### 1. Add Repository Description

On GitHub:
1. Go to your repository
2. Click "About" (gear icon)
3. Add description: "Enterprise-grade RAG chatbot for company policies"
4. Add topics: `chatbot`, `flask`, `ai`, `rag`, `semantic-search`

### 2. Add Repository Topics

Suggested topics:
- `python`
- `flask`
- `chatbot`
- `ai`
- `machine-learning`
- `semantic-search`
- `rag`
- `pdf-processing`
- `sentence-transformers`

### 3. Enable GitHub Pages (Optional)

For documentation:
1. Go to Settings → Pages
2. Select branch: `main`
3. Select folder: `/docs` or `/`
4. Save

### 4. Add Badges to README

Already included in README.md:
- Python version badge
- Flask version badge
- License badge

### 5. Create Releases

1. Go to "Releases" → "Create a new release"
2. Tag: `v1.0.0`
3. Title: "Oudience AI Assistant v1.0.0"
4. Description: List features and changes
5. Publish release

---

## Troubleshooting

### Error: "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/yourusername/your-repo-name.git
```

### Error: "failed to push some refs"
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Error: "Permission denied"
```bash
# Use personal access token instead of password
# Generate at: https://github.com/settings/tokens
```

### Large Files Error
```bash
# If you accidentally added large files:
git rm --cached uploads_exp/*.pdf
git commit -m "Remove large PDF files"
git push
```

---

## Verification Checklist

After uploading, verify:

- [ ] README.md displays correctly
- [ ] .gitignore is working (no sensitive files uploaded)
- [ ] All necessary files are present
- [ ] Documentation is readable
- [ ] License file is included
- [ ] Requirements.txt is complete
- [ ] Example files are provided
- [ ] No passwords or tokens in code

---

## Next Steps

### 1. Share Your Repository
```
https://github.com/yourusername/your-repo-name
```

### 2. Add Collaborators
Settings → Collaborators → Add people

### 3. Set Up GitHub Actions (Optional)
Create `.github/workflows/python-app.yml` for CI/CD

### 4. Enable Issues
Settings → Features → Issues (checkbox)

### 5. Create Wiki (Optional)
For additional documentation

---

## Quick Reference Commands

```bash
# Check status
git status

# Add files
git add .

# Commit changes
git commit -m "Your message"

# Push to GitHub
git push

# Pull latest changes
git pull

# View commit history
git log

# Create new branch
git checkout -b feature-name

# Switch branches
git checkout main
```

---

## Need Help?

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **GitHub Desktop Help**: https://docs.github.com/en/desktop

---

**Ready to upload?** Follow the steps above and your project will be on GitHub! 🚀
