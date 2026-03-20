#!/bin/bash
# Verify EnvisionPerdido Setup
# Purpose: Check that all prerequisites for running the pipeline are met
# Usage: ./scripts/verify-setup.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "EnvisionPerdido Setup Verification"
echo "==================================="

# Check .env exists
if [ ! -f .env ]; then
    log_error ".env file not found"
    log_warn "Create from template: cp .env.example .env"
    exit 1
fi
log_info ".env file exists"

# Check virtual environment
if [ ! -d .venvEnvisionPerdido ]; then
    log_error "Virtual environment not found at .venvEnvisionPerdido"
    log_warn "Create with: make setup"
    exit 1
fi
log_info "Virtual environment exists"

# Activate and check Python
. .venvEnvisionPerdido/bin/activate

PYTHON_VERSION=$(python --version 2>&1)
log_info "Python: $PYTHON_VERSION"

# Check required packages
required_packages=("requests" "sklearn" "icalendar" "python_wordpress_xmlrpc")
missing_packages=()

for pkg in "${required_packages[@]}"; do
    if ! python -c "import ${pkg//-/_}" 2>/dev/null; then
        missing_packages+=("$pkg")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    log_error "Missing Python packages:"
    for pkg in "${missing_packages[@]}"; do
        echo "  - $pkg"
    done
    log_warn "Install with: make install"
    exit 1
fi
log_info "All required Python packages installed"

# Check .env variables
echo ""
echo "Checking environment variables..."

required_vars=("WP_SITE_URL" "WP_USERNAME" "WP_APP_PASSWORD" "SENDER_EMAIL" "RECIPIENT_EMAIL" "SMTP_SERVER" "SMTP_PORT")
missing_vars=()

for var in "${required_vars[@]}"; do
    value=$(grep "^${var}=" .env | cut -d '=' -f 2 | tr -d '"' || echo "")
    if [ -z "$value" ] || [ "$value" = "your_"* ]; then
        missing_vars+=("$var")
    else
        log_info "$var: ***hidden***"
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    log_error "Missing or unconfigured environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    log_warn "Edit .env and set all required variables"
    exit 1
fi

# Check model artifacts
echo ""
echo "Checking model artifacts..."

artifacts=("data/artifacts/event_classifier_model.pkl" "data/artifacts/event_vectorizer.pkl")
missing_artifacts=()

for artifact in "${artifacts[@]}"; do
    if [ ! -f "$artifact" ]; then
        missing_artifacts+=("$artifact")
    else
        size=$(ls -lh "$artifact" | awk '{print $5}')
        log_info "$artifact ($size)"
    fi
done

if [ ${#missing_artifacts[@]} -gt 0 ]; then
    log_error "Missing model artifacts:"
    for artifact in "${missing_artifacts[@]}"; do
        echo "  - $artifact"
    done
    log_warn "Train models using: python scripts/auto_label_and_train.py"
    exit 1
fi

# All checks passed
echo ""
echo "==================================="
log_info "Setup verification complete!"
log_info "You can now run:"
log_info "  make dry-run       # Safe test (no uploads)"
log_info "  make run-pipeline  # Full automation"
