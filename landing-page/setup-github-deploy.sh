#!/bin/bash

# Script to help set up GitHub and deploy to Vercel

echo "🚀 Setting up GitHub repository for deployment"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git not initialized. Run: git init"
    exit 1
fi

echo "📝 Current git status:"
git status --short

echo ""
echo "📦 To deploy via Vercel web interface:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Name it: lexicraft-landing (or any name you prefer)"
echo "   - Don't initialize with README, .gitignore, or license"
echo "   - Click 'Create repository'"
echo ""
echo "2. After creating the repo, GitHub will show you commands."
echo "   Run these commands (replace YOUR_USERNAME and REPO_NAME):"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Then go to https://vercel.com and:"
echo "   - Click 'Add New Project'"
echo "   - Import your GitHub repository"
echo "   - Vercel will auto-detect Next.js"
echo "   - Click 'Deploy'"
echo ""
echo "4. After deployment, add environment variables in Vercel dashboard"
echo "   (See DEPLOY_NOW.md for details)"
echo ""

read -p "Do you want to create the GitHub repo URL now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    read -p "Enter your GitHub username: " GITHUB_USER
    read -p "Enter your repository name (default: lexicraft-landing): " REPO_NAME
    REPO_NAME=${REPO_NAME:-lexicraft-landing}
    
    echo ""
    echo "Run these commands:"
    echo "  git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git"
    echo "  git branch -M main"
    echo "  git push -u origin main"
    echo ""
    echo "Then deploy at: https://vercel.com/new"
fi

