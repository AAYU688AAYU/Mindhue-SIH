#!/usr/bin/env bash
set -e

# ANSI Color Codes
BOLD="\033[1m"
GREEN="\033[1;32m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo -e "\n${BLUE}================================================================${RESET}"
echo -e "${BOLD}${CYAN}   MINDHUE TELE-RETINA COMPREHENSIVE AUTOMATED TEST RUNNER       ${RESET}"
echo -e "${BLUE}================================================================${RESET}\n"

# 1. FRONTEND LINT & TYPE CHECK
echo -e "${YELLOW}[1/4] Running Frontend Linter (oxlint)...${RESET}"
cd "$ROOT_DIR/frontend"
npm run lint
echo -e "${GREEN}✓ Frontend Lint checks passed with zero errors!${RESET}\n"

# 2. FRONTEND PRODUCTION BUILD & CHUNK VERIFICATION
echo -e "${YELLOW}[2/4] Validating Frontend Production Build & Code Splitting...${RESET}"
npm run build
echo -e "${GREEN}✓ Frontend production bundle compiled successfully with code-split lazy chunks!${RESET}\n"

# 3. FRONTEND UNIT & INTEGRATION TESTS
echo -e "${YELLOW}[3/4] Running Frontend Unit & Clinical Logic Tests (node:test)...${RESET}"
cd "$ROOT_DIR"
node --test testing/frontend/*.test.js
echo -e "${GREEN}✓ All Frontend unit tests passed!${RESET}\n"

# 4. BACKEND INTEGRATION, AI PIPELINE & MODEL TESTS
echo -e "${YELLOW}[4/4] Running Backend API, Clinical AI & PyTorch Model Tests...${RESET}"
./venv/bin/python testing/run_backend_tests.py
echo -e "${GREEN}✓ All Backend API endpoints and Deep Learning pipeline tests passed!${RESET}\n"

echo -e "${BLUE}================================================================${RESET}"
echo -e "${BOLD}${GREEN}   ✓ ALL TESTS PASSED SUCCESSFULLY! (100% SUITE VERIFICATION)   ${RESET}"
echo -e "${BLUE}================================================================${RESET}\n"
