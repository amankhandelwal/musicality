#!/usr/bin/env bash
set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()  { printf "${BLUE}ℹ ${NC}%s\n" "$1"; }
ok()    { printf "${GREEN}✔ ${NC}%s\n" "$1"; }
warn()  { printf "${YELLOW}⚠ ${NC}%s\n" "$1"; }
fail()  { printf "${RED}✘ ${NC}%s\n" "$1"; }
header(){ printf "\n${BOLD}── %s ──${NC}\n" "$1"; }

# ── Prerequisite checks ─────────────────────────────────────────────────────
header "Checking prerequisites"
MISSING=0

# macOS-specific checks
if [[ "$(uname)" == "Darwin" ]]; then
    if xcode-select -p &>/dev/null; then
        ok "Xcode CLI Tools"
    else
        fail "Xcode CLI Tools not found — run: xcode-select --install"
        MISSING=1
    fi

    if command -v brew &>/dev/null; then
        ok "Homebrew ($(brew --version | head -1))"
    else
        fail "Homebrew not found — see https://brew.sh"
        MISSING=1
    fi
fi

# Python 3.10–3.12
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER="$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')"
        PY_MAJOR="${PY_VER%%.*}"
        PY_MINOR="${PY_VER##*.}"
        if [[ "$PY_MAJOR" == "3" && "$PY_MINOR" -ge 10 && "$PY_MINOR" -le 12 ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done
if [[ -n "$PYTHON_CMD" ]]; then
    ok "Python ($($PYTHON_CMD --version))"
else
    fail "Python 3.10–3.12 not found — install via pyenv or brew install python@3.12"
    MISSING=1
fi

# Node.js 18+
if command -v node &>/dev/null; then
    NODE_VER="$(node --version | grep -oE '[0-9]+' | head -1)"
    if [[ "$NODE_VER" -ge 18 ]]; then
        ok "Node.js ($(node --version))"
    else
        fail "Node.js 18+ required (found $(node --version)) — upgrade via nvm or brew"
        MISSING=1
    fi
else
    fail "Node.js not found — install via nvm or brew install node"
    MISSING=1
fi

# npm
if command -v npm &>/dev/null; then
    ok "npm ($(npm --version))"
else
    fail "npm not found — comes with Node.js"
    MISSING=1
fi

# uv
if command -v uv &>/dev/null; then
    ok "uv ($(uv --version))"
else
    fail "uv not found — install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    MISSING=1
fi

# FFmpeg
if command -v ffmpeg &>/dev/null; then
    ok "FFmpeg"
else
    fail "FFmpeg not found — install: brew install ffmpeg"
    MISSING=1
fi

# make
if command -v make &>/dev/null; then
    ok "make"
else
    fail "make not found — install Xcode CLI Tools or brew install make"
    MISSING=1
fi

if [[ "$MISSING" -ne 0 ]]; then
    printf "\n${RED}${BOLD}Missing prerequisites — fix the issues above and re-run.${NC}\n"
    exit 1
fi

# ── Backend setup ────────────────────────────────────────────────────────────
header "Setting up backend"
cd "$BACKEND_DIR"

info "Creating virtual environment..."
uv venv

info "Installing build dependencies (cython, numpy, setuptools) for madmom..."
uv pip install cython 'numpy<2.0' 'setuptools<81'

info "Running uv sync (this may take a while on first run)..."
uv sync

ok "Backend ready"

# ── Frontend setup ───────────────────────────────────────────────────────────
header "Setting up frontend"
cd "$FRONTEND_DIR"

info "Installing npm packages..."
npm install

ok "Frontend ready"

# ── Done ─────────────────────────────────────────────────────────────────────
header "Setup complete"
printf "\n"
info "Run the app with:"
printf "  ${BOLD}make start-be${NC}   — backend  at http://localhost:8000\n"
printf "  ${BOLD}make start-fe${NC}   — frontend at http://localhost:5173\n"
printf "  ${BOLD}make stop${NC}       — stop both\n"
printf "\n"
