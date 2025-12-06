#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# ------------------------------------------------------------------
# AUTOMATION SCRIPT for Claude Code (Termux) to harden & validate Adaptheon
#
# --- ADAPTHEON IDENTITY + INTENT (for Claude interpretation) ---
#
# Adaptheon is an evolving modular intelligence system composed of:
# - A Meta-Cognitive Core that orchestrates all modules
# - A Hierarchical Routing Mind (HRM) that determines which subsystem handles a query
# - A Knowledge Scout that retrieves verified factual information
# - A local LLM (via llama.cpp) that provides generative reasoning
# - A Memory Engine (episodic + semantic + vector store)
# - A Tool & Fetcher ecosystem using API-based domain experts
#
# When a user asks "Who are you?", Adaptheon should answer
# something like:
#   "I am Adaptheon, a modular reasoning system built to explore,
#    learn, and adapt. I combine a meta-core, a hierarchical router,
#    domain tools, external knowledge, and a local LLM working
#    together to understand questions and generate grounded answers."
#
# When asked:
#   "What can you do?"
# It should reply in its own words with:
#   "I can analyze questions, search structured knowledge sources,
#    consult domain tools, run local models, retrieve facts, and
#    synthesize reasoning — all coordinated by my meta-core."
#
# When asked:
#   "How do you work?"
# It should answer along the lines of:
#   "I route queries through specialized modules. My Knowledge Scout
#    checks authoritative sources, my LLM performs reasoning, and my
#    memory engines track context. The meta-core orchestrates these
#    pieces so I can adapt over time."
#
# IMPORTANT INSTRUCTION FOR CLAUDE:
# - Inspect the entire Adaptheon project under $REPO (no cloning or
#   directory creation — the repo already exists on disk).
# - Ensure all modules align with the above conceptual blueprint.
# - If anything is missing, stubbed, miswired, or broken, CREATE WHAT
#   IS NEEDED so that every module is a fully working, production-
#   ready, commercial-grade, state-of-the-art implementation, not a
#   placeholder.
# - Ensure llama.cpp (or compatible runtime) integration is correct
#   and fully functional.
# - Ensure identity-questions are recognized even when phrased
#   differently (e.g., "what are you?", "what's your architecture?",
#   "how do you operate?", "describe your design?", etc.), with slight
#   natural variation in wording each time.
# - Ensure the local LLM stack loads the Qwen model as the PRIMARY
#   model for all reasoning, with the Gemma-3-1B instruct model
#   correctly configured and tested as a robust FALLBACK.
# - For every configured web service/domain below, craft and send
#   DIRECT QUESTIONS to Adaptheon (via its normal query path) that
#   force it to use that service. Validate that responses are accurate,
#   grounded, and consistent with the intended API/domain.
# - Expand and refine tests until coverage includes every service type
#   (finance, weather, sports, science, books, media, music, flights,
#   corporate, crime, politics, etc.) and both models (Qwen primary,
#   Gemma fallback) are exercised.
#
# ------------------------------------------------------------------

REPO="$HOME/Adaptheon"
SRC="$REPO/src"
FETCHERS_DIR="$SRC/components/fetchers"
ENV_FILE="$REPO/.env"
DATA_DIR="$REPO/data"
MODELS_DIR="$REPO/models"
REPORT="$REPO/adaptheon_validation_report.md"
QLIST="$REPO/.adaptheon_test_queries.json"
MIN_ACCURACY=0.85

# 1) Exhaustive list of services/domains (primary & fallbacks)
declare -A SERVICES
SERVICES=(
  # General Knowledge
  [wikidata]="https://query.wikidata.org/sparql"
  [wikipedia]="https://en.wikipedia.org/wiki/Special:Search"
  [dbpedia]="https://dbpedia.org/sparql"
  # Politics/Gov
  [usa_gov]="https://api.usa.gov"
  [data_gov]="https://api.data.gov"
  [gov_uk]="https://api.gov.uk"
  # Finance/Crypto
  [yahoo_finance]="https://query1.finance.yahoo.com"
  [alpha_vantage]="https://www.alphavantage.co"
  [finnhub]="https://finnhub.io/api"
  [coingecko]="https://api.coingecko.com/api/v3"
  [coinmarketcap]="https://pro-api.coinmarketcap.com"
  # Weather/Location
  [open_meteo]="https://api.open-meteo.com/v1"
  [noaa]="https://api.weather.gov"
  [nominatim]="https://nominatim.openstreetmap.org"
  # Sports
  [espn]="https://site.api.espn.com/apis/site/v2"
  [thesportsdb]="https://www.thesportsdb.com/api/v1/json"
  # Science/Academic
  [semantic_scholar]="https://api.semanticscholar.org/graph/v1"
  [arxiv]="http://export.arxiv.org/api/query"
  # Books/Media/Music
  [openlibrary]="https://openlibrary.org/search.json"
  [tmdb]="https://api.themoviedb.org/3"
  [tvmaze]="https://api.tvmaze.com"
  [musicbrainz]="https://musicbrainz.org/ws/2"
  # Transportation/Flights
  [aviationstack]="https://api.aviationstack.com/v1"
  [opensky]="https://opensky-network.org/api"
  # Business/Corporate
  [opencorporates]="https://api.opencorporates.com/v0.4"
  # Crime/Justice
  [fbi_cde]="https://api.usa.gov/crime/fbi/sapi"
  # Trending / News / Social / Dev
  [reuters_rss]="https://www.reutersagency.com/feed/?best-topics=politics"
  [ap_rss]="https://apnews.com/hub/politics?outputType=xml"
  [reddit_api]="https://www.reddit.com"
  [github_api]="https://api.github.com"
  [huggingface]="https://huggingface.co"
  [arxiv_rss]="http://export.arxiv.org/api/query"
  # Additional authoritative portals
  [worldbank]="https://api.worldbank.org"
  [eurostat]="https://api.europa.eu"
  [who]="https://www.who.int/data/gho/info/gho-odata-api"
)

# 2) Repo must already exist; do NOT create/clone here
if [ ! -d "$REPO" ]; then
  echo "[-] Repo directory $REPO not found. Please ensure Adaptheon is already checked out there."
  exit 1
fi
cd "$REPO"

# 3) Create source layout if missing (directories only)
mkdir -p "$FETCHERS_DIR" "$DATA_DIR" "$MODELS_DIR" "$SRC/components" "$SRC/components/fetchers"

# 4) Add/ensure requirements-truth.txt exists & basic deps
REQ="$REPO/requirements-truth.txt"
if [ ! -f "$REQ" ]; then
  cat > "$REQ" <<'PYREQ'
requests
SPARQLWrapper
feedparser
pyyaml
python-dotenv
yfinance
pycoingecko
rapidfuzz
qdrant-client
# Add other fetcher libs as needed for production-grade integrations.
PYREQ
  echo "[+] Created $REQ"
fi

echo "[+] Installing core pip deps (requests, SPARQLWrapper, feedparser, rapidfuzz, python-dotenv, yfinance, pycoingecko)..."
pip install --upgrade pip || true
pip install requests SPARQLWrapper feedparser rapidfuzz python-dotenv yfinance pycoingecko || true
# 5) Ensure .env exists with placeholders for API keys and model paths
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'ENV'
# Adaptheon .env - fill the API keys as needed
PERPLEXITY_API_KEY=
TMDB_API_KEY=
ALPHA_VANTAGE_KEY=
FINNHUB_KEY=
COINMARKETCAP_KEY=
AVIATIONSTACK_KEY=
OPENWEATHERMAP_KEY=
QWEN_MODEL_PATH=      # absolute path to primary Qwen GGUF model
GEMMA_MODEL_PATH=     # absolute path to Gemma-3-1B instruct GGUF (fallback)
ENV
  echo "[+] Created placeholder .env at $ENV_FILE"
fi

# export .env into environment for this run
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs) || true
fi

echo "[+] Automation script execution complete - Claude will now analyze and harden the system"
