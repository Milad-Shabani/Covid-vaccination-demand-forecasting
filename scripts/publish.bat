@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM One-shot publish script for Windows: commits everything in
REM this project and pushes it to the GitHub repository below.
REM
REM IMPORTANT: Run this ONLY as scripts\publish.bat, from inside
REM the project folder. Do NOT copy this file elsewhere.
REM ============================================================

set REPO_URL=https://github.com/Milad-Shabani/Covid-vaccination-demand-forecasting.git
set BRANCH=main

cd /d "%~dp0.."

if not exist "requirements.txt" (
  echo ERROR: requirements.txt not found in "%CD%"
  echo This does not look like the project root. Run this file in place,
  echo as scripts\publish.bat - do not move or copy it elsewhere.
  pause
  exit /b 1
)
if not exist "src\malard_vax" (
  echo ERROR: src\malard_vax not found in "%CD%"
  echo This does not look like the project root. Run this file in place,
  echo as scripts\publish.bat - do not move or copy it elsewhere.
  pause
  exit /b 1
)

echo ==^> Working directory: %CD%

echo ==^> Checking that the GitHub repository exists...
git ls-remote %REPO_URL%
if errorlevel 1 (
  echo.
  echo ==^> ERROR: the "git ls-remote" command above failed - see its own
  echo     error message just above this line for the real reason
  echo     ^(e.g. "repository not found" = it doesn't exist yet or is
  echo     private without you being logged in; a network/auth prompt
  echo     that got skipped; wrong URL; etc.^).
  echo.
  echo     If it says "not found": create it fresh at
  echo     https://github.com/new with the exact name
  echo     "covid-vaccination-demand-forecasting" - leave "Add a
  echo     README/.gitignore/license" UNCHECKED so it's completely empty.
  echo     Then run this script again.
  pause
  exit /b 1
)

if not exist ".git" (
  echo ==^> No local git repo yet. Initializing and syncing with GitHub first...
  git init
  git remote add origin %REPO_URL%
  git fetch origin
  if errorlevel 1 (
    echo ERROR: could not reach %REPO_URL%. Check your internet connection and try again.
    pause
    exit /b 1
  )
  git ls-remote --exit-code --heads origin %BRANCH% >nul 2>&1
  if errorlevel 1 (
    echo ==^> Remote has no %BRANCH% branch yet - starting fresh history.
    git checkout -b %BRANCH%
  ) else (
    echo ==^> Basing local repo on the existing origin/%BRANCH% history...
    git checkout -b %BRANCH% origin/%BRANCH%
  )
) else (
  echo ==^> Existing git repository detected.
  git checkout -B %BRANCH%
  git remote get-url origin >nul 2>&1
  if errorlevel 1 (
    git remote add origin %REPO_URL%
  ) else (
    git remote set-url origin %REPO_URL%
  )
)

echo ==^> Staging files...
git add -A

git diff --cached --quiet
if errorlevel 1 (
  echo ==^> Committing...
  git commit -m "Malard VaxForecast: update"
) else (
  echo ==^> Nothing to commit ^(working tree already matches the last commit^).
)

echo ==^> Pushing to origin/%BRANCH%...
git push -u origin %BRANCH%
if errorlevel 1 (
  echo ==^> Push rejected. Pulling and rebasing...
  git pull --rebase origin %BRANCH%
  if errorlevel 1 (
    echo.
    echo ==^> CONFLICT: automatic rebase failed. Aborting to leave your repo clean.
    if exist ".git\rebase-merge" (
      git rebase --abort
    ) else if exist ".git\rebase-apply" (
      git rebase --abort
    )
    echo ==^> Nothing was pushed. This usually means a file was edited both on
    echo     GitHub and locally in a conflicting way, or the remote repository
    echo     URL/name is wrong or was deleted. Please share this output so it
    echo     can be fixed, rather than resolving conflicts by hand.
    pause
    exit /b 1
  )
  git push -u origin %BRANCH%
  if errorlevel 1 (
    echo.
    echo ==^> Push still failed after rebase. Please share this output.
    pause
    exit /b 1
  )
)

echo.
echo ==^> Done. Your repository is now up to date at:
echo     https://github.com/Milad-Shabani/Covid-vaccination-demand-forecasting
pause
