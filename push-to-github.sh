#!/bin/bash

# GitHub Push Script for Mera Business
# This script helps you safely push code to GitHub without exposing secrets

echo "=================================="
echo "Mera Business - GitHub Push Script"
echo "=================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: Not in a git repository!${NC}"
    echo "Run: git init"
    exit 1
fi

echo -e "${GREEN}Step 1: Checking for sensitive files...${NC}"

# Check if .env exists (should not be committed)
if [ -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file found!${NC}"
    # Check if it's in .gitignore
    if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
        echo -e "${RED}CRITICAL: .env is NOT in .gitignore!${NC}"
        echo "Adding .env to .gitignore..."
        echo ".env" >> .gitignore
    else
        echo -e "${GREEN}.env is properly ignored${NC}"
    fi
fi

# Verify .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}Creating .gitignore...${NC}"
    cat > .gitignore << 'EOF'
# Environment variables with secrets
.env

# Python
__pycache__/
*.py[cod]
venv/
*.db
*.db-journal
logs/
*.log

# Media
media/
chat_media/
invoices/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Docker secrets
secrets/
EOF
fi

echo ""
echo -e "${GREEN}Step 2: Checking for hardcoded secrets in code...${NC}"

# Search for potential API keys in Python files
if grep -r "AIzaSy" *.py 2>/dev/null | grep -v ".env.example" | grep -v "your_key_here" | grep -v "#"; then
    echo -e "${RED}DANGER: Found potential API keys in Python files!${NC}"
    echo "Please remove hardcoded keys before committing."
    exit 1
else
    echo -e "${GREEN}No hardcoded secrets found${NC}"
fi

echo ""
echo -e "${GREEN}Step 3: Verifying required files...${NC}"

required_files=("README.md" ".gitignore" ".env.example" "requirements.txt" "Dockerfile" "docker-compose.yml")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo -e "${RED}Missing required files:${NC}"
    printf '%s\n' "${missing_files[@]}"
    exit 1
else
    echo -e "${GREEN}All required files present${NC}"
fi

echo ""
echo -e "${GREEN}Step 4: Staging files...${NC}"

# Add all files except those in .gitignore
git add .

echo ""
echo -e "${YELLOW}Files to be committed:${NC}"
git status --short

echo ""
echo -e "${YELLOW}Review the files above. Press Enter to continue or Ctrl+C to cancel...${NC}"
read

echo ""
echo -e "${GREEN}Step 5: Creating commit...${NC}"

# Ask for commit message
echo "Enter commit message (or press Enter for default):"
read commit_message

if [ -z "$commit_message" ]; then
    commit_message="Update: Production-ready Docker setup with documentation"
fi

git commit -m "$commit_message"

echo ""
echo -e "${GREEN}Step 6: Checking remote repository...${NC}"

# Check if remote exists
if ! git remote | grep -q "origin"; then
    echo -e "${YELLOW}No remote 'origin' found.${NC}"
    echo "Enter your GitHub repository URL (e.g., https://github.com/pablo-2047/Mera-Business.git):"
    read repo_url
    
    if [ -n "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo -e "${GREEN}Remote added: $repo_url${NC}"
    else
        echo -e "${RED}No URL provided. Skipping remote setup.${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Step 7: Pushing to GitHub...${NC}"

# Get current branch
branch=$(git branch --show-current)

if [ -z "$branch" ]; then
    branch="main"
    git branch -M main
fi

echo "Pushing to branch: $branch"

# Try to push
if git push -u origin "$branch"; then
    echo ""
    echo -e "${GREEN}=================================="
    echo "✅ Successfully pushed to GitHub!"
    echo -e "==================================${NC}"
    echo ""
    echo "Your repository is now updated with:"
    echo "✅ Production-ready Dockerfile"
    echo "✅ Docker Compose configuration"
    echo "✅ Comprehensive README"
    echo "✅ Security documentation"
    echo "✅ Judge quickstart guide"
    echo "✅ .gitignore (protecting secrets)"
    echo ""
    echo "Repository URL: $(git remote get-url origin)"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Visit your GitHub repository"
    echo "2. Verify README looks good"
    echo "3. Consider deploying to Railway/Render"
    echo "4. Share the repository link with judges"
else
    echo ""
    echo -e "${RED}Push failed!${NC}"
    echo "This might be because:"
    echo "1. You need to authenticate (run: gh auth login)"
    echo "2. The repository doesn't exist yet"
    echo "3. You don't have permission"
    echo ""
    echo "To manually push, run:"
    echo "  git push -u origin $branch"
fi

echo ""
echo -e "${GREEN}=================================="
echo "Script completed!"
echo -e "==================================${NC}"
