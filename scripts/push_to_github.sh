#!/usr/bin/env bash
# Usage: ./scripts/push_to_github.sh <your-github-username>
# Example: ./scripts/push_to_github.sh yashpatil582

set -e

GITHUB_USER=${1:-yashpatil582}
REPO_NAME="fintech-decisioning-agent"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo "→ Initialising git..."
git init
git add -A
git commit -m "feat: initial implementation — LangChain agent on AWS Bedrock with FastAPI, FAISS RAG, EKS deployment"

echo "→ Pushing to ${REPO_URL}"
echo "   Make sure you've created the repo on GitHub first:"
echo "   https://github.com/new  (name: ${REPO_NAME}, public, NO readme/gitignore)"
echo ""
read -p "Press Enter when the GitHub repo is created..."

git branch -M main
git remote add origin ${REPO_URL}
git push -u origin main

echo "✅ Done! Repo live at https://github.com/${GITHUB_USER}/${REPO_NAME}"
