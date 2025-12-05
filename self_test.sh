#!/usr/bin/env bash
# Adaptheon Phase 2.0 - Self-Test Script
# Tests all components and verifies system integrity

ADAPTHEON_HOME="$HOME/Adaptheon"
FAILURES=0
TESTS_RUN=0

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Adaptheon Phase 2.0 - Self-Test      ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

cd "$ADAPTHEON_HOME" || exit 1

# Test function
test_check() {
    local test_name="$1"
    local test_command="$2"

    ((TESTS_RUN++))
    echo -n "Testing: $test_name... "

    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILURES++))
        return 1
    fi
}

# 1. Directory Structure Tests
echo -e "${YELLOW}[1] Directory Structure Tests${NC}"
test_check "Adaptheon home exists" "[ -d '$ADAPTHEON_HOME' ]"
test_check "src directory exists" "[ -d '$ADAPTHEON_HOME/src' ]"
test_check "data/memory exists" "[ -d '$ADAPTHEON_HOME/data/memory' ]"
test_check "data/cache exists" "[ -d '$ADAPTHEON_HOME/data/cache' ]"
test_check "data/corpus exists" "[ -d '$ADAPTHEON_HOME/data/corpus' ]"
test_check "models directory exists" "[ -d '$ADAPTHEON_HOME/models' ]"
test_check "llama.cpp directory exists" "[ -d '$ADAPTHEON_HOME/llama.cpp' ]"
echo ""

# 2. Python Module Tests
echo -e "${YELLOW}[2] Python Module Tests${NC}"
test_check "Python is available" "command -v python"
test_check "NumPy is installed" "python -c 'import numpy'"
test_check "Requests is installed" "python -c 'import requests'"
test_check "BeautifulSoup4 is installed" "python -c 'import bs4'"
test_check "Feedparser is installed" "python -c 'import feedparser'"
echo ""

# 3. Core Python Files Tests
echo -e "${YELLOW}[3] Core Python Files Tests${NC}"
test_check "main.py exists" "[ -f '$ADAPTHEON_HOME/main.py' ]"
test_check "src/meta_core.py exists" "[ -f '$ADAPTHEON_HOME/src/meta_core.py' ]"
test_check "src/__init__.py exists" "[ -f '$ADAPTHEON_HOME/src/__init__.py' ]"
test_check "components/__init__.py exists" "[ -f '$ADAPTHEON_HOME/src/components/__init__.py' ]"
echo ""

# 4. Component Files Tests
echo -e "${YELLOW}[4] Component Files Tests${NC}"
test_check "memory.py exists" "[ -f '$ADAPTHEON_HOME/src/components/memory.py' ]"
test_check "llm_interface.py exists" "[ -f '$ADAPTHEON_HOME/src/components/llm_interface.py' ]"
test_check "hrm.py exists" "[ -f '$ADAPTHEON_HOME/src/components/hrm.py' ]"
test_check "knowledge_scout.py exists" "[ -f '$ADAPTHEON_HOME/src/components/knowledge_scout.py' ]"
test_check "semantic_utils.py exists" "[ -f '$ADAPTHEON_HOME/src/components/semantic_utils.py' ]"
test_check "price_service.py exists" "[ -f '$ADAPTHEON_HOME/src/components/price_service.py' ]"
test_check "weather_service.py exists" "[ -f '$ADAPTHEON_HOME/src/components/weather_service.py' ]"
test_check "location_service.py exists" "[ -f '$ADAPTHEON_HOME/src/components/location_service.py' ]"
echo ""

# 5. Python Import Tests
echo -e "${YELLOW}[5] Python Import Tests${NC}"
test_check "Can import meta_core" "cd '$ADAPTHEON_HOME' && python -c 'import sys; sys.path.insert(0, \"src\"); from meta_core import MetaCognitiveCore'"
test_check "Can import components.memory" "cd '$ADAPTHEON_HOME' && python -c 'import sys; sys.path.insert(0, \"src\"); from components.memory import MemorySystem'"
test_check "Can import components.llm_interface" "cd '$ADAPTHEON_HOME' && python -c 'import sys; sys.path.insert(0, \"src\"); from components.llm_interface import LanguageSystem'"
test_check "Can import components.hrm" "cd '$ADAPTHEON_HOME' && python -c 'import sys; sys.path.insert(0, \"src\"); from components.hrm import HierarchicalReasoningMachine'"
test_check "Can import components.knowledge_scout" "cd '$ADAPTHEON_HOME' && python -c 'import sys; sys.path.insert(0, \"src\"); from components.knowledge_scout import KnowledgeScout'"
echo ""

# 6. Knowledge Scout Module Tests
echo -e "${YELLOW}[6] Knowledge Scout Module Tests${NC}"
test_check "knowledge_scout/__init__.py exists" "[ -f '$ADAPTHEON_HOME/src/knowledge_scout/__init__.py' ]"
test_check "fetchers/base.py exists" "[ -f '$ADAPTHEON_HOME/src/knowledge_scout/fetchers/base.py' ]"
test_check "fetchers/wikipedia_fetcher.py exists" "[ -f '$ADAPTHEON_HOME/src/knowledge_scout/fetchers/wikipedia_fetcher.py' ]"
test_check "fetchers/rss_fetcher.py exists" "[ -f '$ADAPTHEON_HOME/src/knowledge_scout/fetchers/rss_fetcher.py' ]"
test_check "fetchers/local_corpus_fetcher.py exists" "[ -f '$ADAPTHEON_HOME/src/knowledge_scout/fetchers/local_corpus_fetcher.py' ]"
echo ""

# 7. Regex Pattern Tests (Critical Bug Fixes)
echo -e "${YELLOW}[7] Regex Pattern Validation Tests${NC}"
test_check "semantic_utils.py regex is correct" "grep -q 'r\"\\\\w+\"' '$ADAPTHEON_HOME/src/components/semantic_utils.py'"
test_check "local_corpus_fetcher.py regex is correct" "grep -q 'r\"\\\\w+\"' '$ADAPTHEON_HOME/src/knowledge_scout/fetchers/local_corpus_fetcher.py'"
test_check "wikipedia_fetcher.py citation regex is correct" "grep -q 'r\"\\\\\\[\\\\d+\\\\\\]\"' '$ADAPTHEON_HOME/src/knowledge_scout/fetchers/wikipedia_fetcher.py'"
test_check "wikipedia_fetcher.py whitespace regex is correct" "grep -q 'r\"\\\\s+\"' '$ADAPTHEON_HOME/src/knowledge_scout/fetchers/wikipedia_fetcher.py'"
echo ""

# 8. llama.cpp Build Tests
echo -e "${YELLOW}[8] llama.cpp Build Tests${NC}"
test_check "llama.cpp cloned" "[ -d '$ADAPTHEON_HOME/llama.cpp/.git' ]"
test_check "llama.cpp build directory exists" "[ -d '$ADAPTHEON_HOME/llama.cpp/build' ]"
test_check "llama-cli binary exists" "[ -f '$ADAPTHEON_HOME/llama.cpp/build/bin/llama-cli' ]"
test_check "llama-cli is executable" "[ -x '$ADAPTHEON_HOME/llama.cpp/build/bin/llama-cli' ]"
echo ""

# 9. Data Files Tests
echo -e "${YELLOW}[9] Data Files Tests${NC}"
test_check "core_memory.json exists" "[ -f '$ADAPTHEON_HOME/data/memory/core_memory.json' ]"
test_check "knowledge_cache.json exists" "[ -f '$ADAPTHEON_HOME/data/cache/knowledge_cache.json' ]"
test_check "disputes.json exists" "[ -f '$ADAPTHEON_HOME/data/memory/disputes.json' ]"
echo ""

# 10. Functional Test - Import and Initialize
echo -e "${YELLOW}[10] Functional Integration Test${NC}"
test_check "MetaCognitiveCore instantiation" "cd '$ADAPTHEON_HOME' && python -c '
import sys
sys.path.insert(0, \"src\")
from meta_core import MetaCognitiveCore
core = MetaCognitiveCore()
print(\"Core initialized successfully\")
' 2>&1 | grep -q 'initialized'"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Test Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Tests Run:    ${TESTS_RUN}"
echo -e "Tests Passed: $((TESTS_RUN - FAILURES))"
echo -e "Tests Failed: ${FAILURES}"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Adaptheon is ready.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review errors above.${NC}"
    exit 1
fi
