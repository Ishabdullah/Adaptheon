#!/usr/bin/env bash
# Adaptheon Phase 2.0 - Termux Run Script

set -e

ADAPTHEON_HOME="$HOME/Adaptheon"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Adaptheon Phase 2.0 - Starting     ${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Change to Adaptheon directory
cd "$ADAPTHEON_HOME" || {
    echo -e "${RED}Error: Cannot change to Adaptheon directory${NC}"
    exit 1
}

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python --version || {
    echo -e "${RED}Error: Python not found${NC}"
    exit 1
}

# Check dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
python -c "import numpy, requests, bs4, feedparser" 2>/dev/null || {
    echo -e "${RED}Error: Missing Python dependencies. Installing...${NC}"
    pip install -r requirements.txt
}

# Check llama.cpp binary
LLAMA_BIN="$ADAPTHEON_HOME/llama.cpp/build/bin/llama-cli"
if [ -f "$LLAMA_BIN" ]; then
    echo -e "${GREEN}✓ llama-cli found at: $LLAMA_BIN${NC}"
else
    echo -e "${YELLOW}⚠ llama-cli not found. Running in simulation mode.${NC}"
    echo -e "${YELLOW}  To enable LLM: Build llama.cpp and download a model${NC}"
fi

# Create necessary directories
mkdir -p data/memory data/cache data/corpus models/qwen

echo ""
echo -e "${GREEN}Starting Adaptheon Meta-Cognitive Core...${NC}"
echo ""

# Run Adaptheon
python main.py "$@"
