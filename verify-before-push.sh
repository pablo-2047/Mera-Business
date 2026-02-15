#!/bin/bash

# Final verification script before GitHub push
# This checks everything is configured correctly

echo "=========================================="
echo "Pre-Push Security & Quality Verification"
echo "=========================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "🔍 Checking security..."
echo ""

# 1. Check .env is in .gitignore
echo -n "1. Checking .gitignore has .env... "
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Missing!${NC}"
    ((ERRORS++))
fi

# 2. Check .env is NOT committed
echo -n "2. Checking .env is not in git... "
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo -e "${RED}✗ DANGER: .env is tracked by git!${NC}"
    echo "   Run: git rm --cached .env"
    ((ERRORS++))
else
    echo -e "${GREEN}✓${NC}"
fi

# 3. Check for API keys in Python files
echo -n "3. Checking for hardcoded API keys... "
if grep -r "AIzaSy" *.py 2>/dev/null | grep -v ".env.example" | grep -v "your_key" | grep -v "#"; then
    echo -e "${RED}✗ Found API keys in code!${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓${NC}"
fi

# 4. Check .env.example has placeholders only
echo -n "4. Checking .env.example is safe... "
if grep -q "AIzaSyDv9zwd2Qo6yCdQu60R_SbV7WhFzJ5uzUM" .env.example 2>/dev/null; then
    echo -e "${RED}✗ Real API key in .env.example!${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓${NC}"
fi

echo ""
echo "📁 Checking required files..."
echo ""

required_files=(
    "README.md"
    "JUDGE_QUICKSTART.md"
    "HOW_TO_RUN.md"
    "SECURITY.md"
    "SUBMISSION_CHECKLIST.md"
    ".gitignore"
    ".env.example"
    "Dockerfile"
    "docker-compose.yml"
    ".dockerignore"
    "requirements.txt"
    "app.py"
    "database.py"
    "intent_router.py"
)

missing=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (missing)"
        missing+=("$file")
        ((ERRORS++))
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}Missing files: ${missing[*]}${NC}"
fi

echo ""
echo "🐳 Checking Docker configuration..."
echo ""

# Check Dockerfile
echo -n "1. Dockerfile exists... "
if [ -f "Dockerfile" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    ((ERRORS++))
fi

# Check docker-compose.yml
echo -n "2. docker-compose.yml exists... "
if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    ((ERRORS++))
fi

# Check .dockerignore
echo -n "3. .dockerignore exists... "
if [ -f ".dockerignore" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ Missing (recommended)${NC}"
    ((WARNINGS++))
fi

echo ""
echo "📚 Checking documentation..."
echo ""

# Check README has content
echo -n "1. README has content... "
if [ -s "README.md" ] && [ $(wc -l < README.md) -gt 50 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ README seems short${NC}"
    ((WARNINGS++))
fi

# Check for demo instructions
echo -n "2. README has demo instructions... "
if grep -qi "docker-compose up" README.md 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ Missing Docker instructions${NC}"
    ((WARNINGS++))
fi

echo ""
echo "🧪 Checking test data..."
echo ""

# Check if sample data script exists
echo -n "1. Sample data generator exists... "
if [ -f "generate_sample_data.py" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ No sample data script${NC}"
    ((WARNINGS++))
fi

echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED!${NC}"
    echo ""
    echo "Your project is ready to push to GitHub!"
    echo ""
    echo "Next steps:"
    echo "  git add ."
    echo "  git commit -m 'Production-ready: Docker, docs, security'"
    echo "  git push origin main"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ ${WARNINGS} WARNING(S)${NC}"
    echo ""
    echo "Your project is mostly ready, but has minor issues."
    echo "You can proceed with push, but consider fixing warnings."
    exit 0
else
    echo -e "${RED}✗ ${ERRORS} ERROR(S), ${WARNINGS} WARNING(S)${NC}"
    echo ""
    echo "Please fix the errors above before pushing to GitHub!"
    exit 1
fi
