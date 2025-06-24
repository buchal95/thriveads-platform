#!/bin/bash

# ThriveAds Platform - Deployment Readiness Check
# This script validates that the platform is ready for production deployment

# set -e  # Disabled to allow script to continue on failed checks

echo "🚀 ThriveAds Platform - Deployment Readiness Check"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Helper functions
check_passed() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

check_failed() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

check_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

check_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "thriveads-backend/requirements.txt" ] || [ ! -f "thriveads-client-platform/package.json" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    echo -e "${RED}   Expected to find thriveads-backend/ and thriveads-client-platform/ directories${NC}"
    exit 1
fi

echo ""
echo "🔍 Checking Backend Configuration..."
echo "-----------------------------------"

# Check backend dependencies
if [ -f "thriveads-backend/requirements.txt" ]; then
    check_passed "Backend requirements.txt exists"
else
    check_failed "Backend requirements.txt missing"
fi

# Check backend environment configuration
if [ -f "thriveads-backend/.env.example" ]; then
    check_passed "Backend environment template exists"
else
    check_failed "Backend .env.example missing"
fi

# Check Railway configuration
if [ -f "thriveads-backend/railway.json" ]; then
    check_passed "Railway configuration exists"
else
    check_failed "Railway configuration missing"
fi

# Check Dockerfile
if [ -f "thriveads-backend/Dockerfile" ]; then
    check_passed "Backend Dockerfile exists"
else
    check_failed "Backend Dockerfile missing"
fi

# Check database migrations
if [ -d "thriveads-backend/alembic" ]; then
    check_passed "Database migrations directory exists"
else
    check_failed "Database migrations missing"
fi

echo ""
echo "🎨 Checking Frontend Configuration..."
echo "------------------------------------"

# Check frontend dependencies
if [ -f "thriveads-client-platform/package.json" ]; then
    check_passed "Frontend package.json exists"
else
    check_failed "Frontend package.json missing"
fi

# Check Vercel configuration
if [ -f "thriveads-client-platform/vercel.json" ]; then
    check_passed "Vercel configuration exists"
else
    check_failed "Vercel configuration missing"
fi

# Check Next.js configuration
if [ -f "thriveads-client-platform/next.config.ts" ]; then
    check_passed "Next.js configuration exists"
else
    check_failed "Next.js configuration missing"
fi

# Check Tailwind configuration
if [ -f "thriveads-client-platform/tailwind.config.ts" ]; then
    check_passed "Tailwind configuration exists"
else
    check_warning "Tailwind configuration missing"
fi

echo ""
echo "🔧 Checking DevOps Configuration..."
echo "----------------------------------"

# Check CI/CD pipeline
if [ -f ".github/workflows/ci.yml" ]; then
    check_passed "CI/CD pipeline configuration exists"
else
    check_failed "CI/CD pipeline missing"
fi

# Check gitignore
if [ -f ".gitignore" ]; then
    check_passed "Root .gitignore exists"
else
    check_warning "Root .gitignore missing"
fi

# Check README
if [ -f "README.md" ]; then
    check_passed "README.md exists"
else
    check_warning "README.md missing"
fi

# Check deployment guide
if [ -f "DEPLOYMENT_GUIDE.md" ]; then
    check_passed "Deployment guide exists"
else
    check_warning "Deployment guide missing"
fi

echo ""
echo "🔐 Checking Security Configuration..."
echo "------------------------------------"

# Check for sensitive files that shouldn't be committed
if [ -f "thriveads-backend/.env" ]; then
    check_warning "Backend .env file exists (ensure it's in .gitignore)"
fi

if [ -f "thriveads-client-platform/.env.local" ]; then
    check_warning "Frontend .env.local file exists (ensure it's in .gitignore)"
fi

# Check CORS configuration
if grep -q "ALLOWED_ORIGINS" thriveads-backend/app/core/config.py 2>/dev/null; then
    check_passed "CORS configuration found"
else
    check_failed "CORS configuration missing"
fi

echo ""
echo "🧪 Checking Test Configuration..."
echo "--------------------------------"

# Check backend tests
if [ -f "thriveads-backend/test_main.py" ] || [ -d "thriveads-backend/tests" ]; then
    check_passed "Backend tests exist"
else
    check_warning "Backend tests missing"
fi

# Check frontend tests
if grep -q "\"test\"" thriveads-client-platform/package.json 2>/dev/null; then
    check_passed "Frontend test script configured"
else
    check_warning "Frontend test script missing"
fi

echo ""
echo "📊 Summary"
echo "=========="
echo -e "✅ Checks passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "❌ Checks failed: ${RED}$CHECKS_FAILED${NC}"
echo -e "⚠️  Warnings: ${YELLOW}$WARNINGS${NC}"

echo ""
if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Platform is ready for deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Ensure environment variables are configured in Vercel and Railway"
    echo "2. Connect GitHub repository to Vercel and Railway"
    echo "3. Test deployment in staging environment"
    echo "4. Monitor deployment logs and health checks"
    exit 0
else
    echo -e "${RED}🚨 Platform is NOT ready for deployment${NC}"
    echo ""
    echo "Please fix the failed checks before deploying to production."
    exit 1
fi
