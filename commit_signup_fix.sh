#!/bin/bash
# Commit only the signup fix changes (not all the other modified files)

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║     Committing Signup Fix Changes                               ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

cd /Users/davidfinney/Downloads/visaguardai

echo "Adding signup fix files to git..."
echo ""

# Add the critical fix files
git add dashboard/models.py
echo "✅ dashboard/models.py"

git add dashboard/signals.py
echo "✅ dashboard/signals.py"

git add dashboard/migrations/0024_alter_userprofile_username.py
echo "✅ dashboard/migrations/0024_alter_userprofile_username.py"

git add deploy_signup_fix.sh
echo "✅ deploy_signup_fix.sh"

git add check_production_logs.sh
echo "✅ check_production_logs.sh"

git add test_signup_fix_local.py
echo "✅ test_signup_fix_local.py"

git add verify_signup_fix.sh
echo "✅ verify_signup_fix.sh"

git add SIGNUP_FIX_REPORT.md
echo "✅ SIGNUP_FIX_REPORT.md"

git add URGENT_SIGNUP_FIX_README.md
echo "✅ URGENT_SIGNUP_FIX_README.md"

git add GIT_COMMIT_MESSAGE.txt
echo "✅ GIT_COMMIT_MESSAGE.txt"

echo ""
echo "Files staged for commit:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git status --short | grep "^A"
echo ""

echo "Creating commit..."
git commit -F GIT_COMMIT_MESSAGE.txt

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ COMMIT CREATED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git push origin main"
echo "2. SSH to production server"
echo "3. Run: ./deploy_signup_fix.sh"
echo ""

