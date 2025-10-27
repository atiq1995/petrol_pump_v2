#!/bin/bash

# Petrol Pump V2 - GitHub Upload Helper Script
# This script helps you push your code to GitHub

echo "================================="
echo " Petrol Pump V2 - GitHub Upload "
echo "================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    
    echo ""
    echo "👤 Please enter your details:"
    read -p "Your Name: " git_name
    read -p "Your Email: " git_email
    
    git config user.name "$git_name"
    git config user.email "$git_email"
    
    echo "✅ Git initialized!"
fi

echo ""
echo "📝 Adding files to Git..."
git add .

echo ""
echo "📋 Files to be committed:"
git status --short

echo ""
read -p "Enter commit message (or press Enter for default): " commit_msg

if [ -z "$commit_msg" ]; then
    commit_msg="Initial commit: Petrol Pump Management System V2"
fi

echo ""
echo "💾 Creating commit..."
git commit -m "$commit_msg"

echo ""
echo "🔗 GitHub Repository Setup"
echo ""
read -p "Have you created a repository on GitHub? (y/n): " has_repo

if [ "$has_repo" != "y" ]; then
    echo ""
    echo "⚠️  Please create a repository on GitHub first:"
    echo "   1. Go to https://github.com/new"
    echo "   2. Repository name: petrol_pump_v2"
    echo "   3. Don't add README, .gitignore, or LICENSE (we have them)"
    echo "   4. Click 'Create repository'"
    echo ""
    read -p "Press Enter when done..."
fi

echo ""
read -p "Enter your GitHub username: " github_username
repo_url="https://github.com/$github_username/petrol_pump_v2.git"

# Check if remote already exists
if git remote | grep -q "origin"; then
    echo "📡 Remote 'origin' already exists. Removing..."
    git remote remove origin
fi

echo "🌐 Adding remote repository..."
git remote add origin "$repo_url"

echo ""
echo "🚀 Pushing to GitHub..."
echo "   (You may be asked for your GitHub username and Personal Access Token)"
echo ""

git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Your code is now on GitHub!"
    echo ""
    echo "📍 Repository URL:"
    echo "   https://github.com/$github_username/petrol_pump_v2"
    echo ""
    echo "📖 Next steps:"
    echo "   - View your repository in a browser"
    echo "   - Add a description and topics"
    echo "   - Share with the community!"
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "   1. Wrong credentials - Use Personal Access Token as password"
    echo "   2. Repository doesn't exist - Create it on GitHub first"
    echo "   3. Network issues - Check your internet connection"
    echo ""
    echo "📚 For help, see GITHUB_SETUP.md"
fi

echo ""
echo "================================="

