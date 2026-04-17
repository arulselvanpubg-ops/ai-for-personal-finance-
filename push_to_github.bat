@echo off
echo ========================================
echo    FinSight AI - GitHub Push Script
echo ========================================
echo.
echo This script will push your code to GitHub.
echo Make sure you have:
echo 1. Created a GitHub repository
echo 2. Updated the remote URL below
echo.
echo Current remote URL:
git remote -v
echo.
echo If the URL shows YOUR_USERNAME, you need to update it first:
echo git remote set-url origin https://github.com/YOUR_ACTUAL_USERNAME/finsight-ai.git
echo.
echo Then run: git push -u origin main
echo.
pause