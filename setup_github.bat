@echo off
echo ========================================
echo Oudience AI Assistant - GitHub Setup
echo ========================================
echo.

REM Initialize git repository
echo [1/5] Initializing Git repository...
git init
echo.

REM Add all files
echo [2/5] Adding files to Git...
git add .
echo.

REM Create initial commit
echo [3/5] Creating initial commit...
git commit -m "Initial commit: Oudience AI Assistant v1.0 - Enterprise RAG chatbot with Flask, semantic search, and professional UI"
echo.

REM Instructions for remote
echo [4/5] Next steps:
echo.
echo Please create a repository on GitHub first, then run:
echo.
echo git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
echo git branch -M main
echo git push -u origin main
echo.

echo [5/5] Setup complete!
echo.
echo ========================================
echo Important: Before pushing to GitHub
echo ========================================
echo 1. Create a new repository on GitHub.com
echo 2. Copy the repository URL
echo 3. Run the commands shown above
echo 4. Make sure to change ADMIN_TOKEN in app.py
echo ========================================
echo.
pause
