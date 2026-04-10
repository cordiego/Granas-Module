#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Granas-Module — GitHub Push Script
# ═══════════════════════════════════════════════════════════
# 1. Create repo on GitHub (if not exists)
# 2. Push to origin
#
# Usage: bash push_to_github.sh
# ═══════════════════════════════════════════════════════════

set -e

REPO="Granas-Module"
USER="cordiego"
REMOTE="https://${USER}@github.com/${USER}/${REPO}.git"

echo "═══════════════════════════════════════════════════"
echo " 🔬 Pushing ${REPO} to GitHub"
echo "═══════════════════════════════════════════════════"

# Ensure remote is set
git remote set-url origin "${REMOTE}" 2>/dev/null || git remote add origin "${REMOTE}"

# Push
echo "📤 Pushing to ${REMOTE}..."
git push -u origin main

echo ""
echo "✅ Done! https://github.com/${USER}/${REPO}"
echo "═══════════════════════════════════════════════════"
