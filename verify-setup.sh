#!/bin/bash

echo "======================================"
echo "E-Commerce Microservices Setup Check"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed ($($1 --version 2>&1 | head -n 1))"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

echo "Checking Prerequisites..."
echo ""

# Check Go
check_command go
GO_OK=$?

# Check Python
check_command python3
PYTHON_OK=$?

# Check Ruby
check_command ruby
RUBY_OK=$?

# Check Git
check_command git
GIT_OK=$?

echo ""
echo "======================================"
echo "Service Structure Check"
echo "======================================"
echo ""

# Check directory structure
if [ -d "auth-service" ]; then
    echo -e "${GREEN}✓${NC} auth-service directory exists"
    if [ -f "auth-service/go.mod" ]; then
        echo -e "  ${GREEN}✓${NC} go.mod found"
    fi
else
    echo -e "${RED}✗${NC} auth-service directory missing"
fi

if [ -d "analytics-service" ]; then
    echo -e "${GREEN}✓${NC} analytics-service directory exists"
    if [ -f "analytics-service/requirements.txt" ]; then
        echo -e "  ${GREEN}✓${NC} requirements.txt found"
    fi
else
    echo -e "${RED}✗${NC} analytics-service directory missing"
fi

if [ -d "api-gateway" ]; then
    echo -e "${GREEN}✓${NC} api-gateway directory exists"
    if [ -f "api-gateway/Gemfile" ]; then
        echo -e "  ${GREEN}✓${NC} Gemfile found"
    fi
else
    echo -e "${RED}✗${NC} api-gateway directory missing"
fi

echo ""
echo "======================================"
echo "CI/CD Configuration Check"
echo "======================================"
echo ""

if [ -d ".github/workflows" ]; then
    echo -e "${GREEN}✓${NC} GitHub Actions workflows directory exists"

    if [ -f ".github/workflows/go-tests.yml" ]; then
        echo -e "  ${GREEN}✓${NC} Go tests workflow configured"
    fi

    if [ -f ".github/workflows/python-tests.yml" ]; then
        echo -e "  ${GREEN}✓${NC} Python tests workflow configured"
    fi

    if [ -f ".github/workflows/ruby-tests.yml" ]; then
        echo -e "  ${GREEN}✓${NC} Ruby tests workflow configured"
    fi
else
    echo -e "${RED}✗${NC} GitHub Actions workflows not configured"
fi

echo ""
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

ALL_OK=0
if [ $GO_OK -eq 0 ] && [ $PYTHON_OK -eq 0 ] && [ $RUBY_OK -eq 0 ] && [ $GIT_OK -eq 0 ]; then
    echo -e "${GREEN}✓ All prerequisites are installed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Read QUICKSTART.md to run the services"
    echo "2. Create a PR to see Codity in action"
    echo "3. Watch automated test generation and CI"
else
    echo -e "${YELLOW}⚠ Some prerequisites are missing${NC}"
    echo ""
    echo "Please install:"
    [ $GO_OK -ne 0 ] && echo "  - Go 1.21+: https://go.dev/dl/"
    [ $PYTHON_OK -ne 0 ] && echo "  - Python 3.11+: https://www.python.org/downloads/"
    [ $RUBY_OK -ne 0 ] && echo "  - Ruby 3.2+: https://www.ruby-lang.org/en/downloads/"
    [ $GIT_OK -ne 0 ] && echo "  - Git: https://git-scm.com/downloads"
    ALL_OK=1
fi

echo ""
exit $ALL_OK
