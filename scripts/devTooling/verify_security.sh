#!/bin/bash
# Security Verification Script
# Run this after rotating your API keys to verify clean state

echo "=================================================="
echo "EnvisionPerdido Security Verification"
echo "=================================================="
echo ""

# 1. Check .env is in .gitignore
echo "[1/5] Checking .gitignore..."
if grep -q "^\.env$" .gitignore; then
    echo "    ✓ .env is protected in .gitignore"
else
    echo "    ✗ WARNING: .env not found in .gitignore!"
fi

# 2. Verify .env is not committed
echo ""
echo "[2/5] Checking if .env is tracked by git..."
if git ls-files | grep -q "^\.env$"; then
    echo "    ✗ ERROR: .env is tracked by git! Remove it:"
    echo "       git rm --cached .env"
    echo "       git commit -m 'Remove .env from tracking'"
else
    echo "    ✓ .env is not tracked by git"
fi

# 3. Search for API key patterns in git history
echo ""
echo "[3/5] Searching for API key patterns in git history..."
echo "    (This may take a moment...)"

search_patterns=(
    "sk-proj-"
    "OPENAI_API_KEY="
    "WP_APP_PASSWORD"
    "EMAIL_PASSWORD"
)

found_any=0
for pattern in "${search_patterns[@]}"; do
    if git log -S "$pattern" --oneline --all 2>/dev/null | grep -q .; then
        echo "    ✗ Found pattern '$pattern' in history!"
        found_any=1
    fi
done

if [ $found_any -eq 0 ]; then
    echo "    ✓ No API key patterns found in git history"
fi

# 4. Check for unencrypted secrets in working directory
echo ""
echo "[4/5] Checking for unencrypted secrets in working directory..."
if [ -f ".env" ]; then
    if grep -q "sk-proj-" .env; then
        echo "    ⚠️  WARNING: Found API key in .env file"
        echo "       Make sure this file is NOT committed to git"
    else
        echo "    ✓ .env file exists but doesn't contain API keys"
    fi
else
    echo "    ℹ  .env file not found (safe - may not be needed now)"
fi

# 5. .env.example check
echo ""
echo "[5/5] Checking .env.example (should have no real secrets)..."
if grep -q "sk-proj-" .env.example 2>/dev/null; then
    echo "    ✗ ERROR: Real API key found in .env.example!"
    echo "       This file should only have placeholders!"
else
    echo "    ✓ .env.example contains only placeholders"
fi

echo ""
echo "=================================================="
echo "Security Verification Complete"
echo "=================================================="
