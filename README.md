# Adaptheon Phase 2.0

Adaptheon is a local‑first cognitive agent framework designed to run entirely on an Android phone using Termux. It combines a lightweight reasoning core, multi‑source retrieval, and a fully offline Qwen GGUF language model running through `llama.cpp` — no remote servers, no cloud APIs.

---

## Features

- **100% on‑device LLM**
  - Uses `Qwen2-1.5B-Instruct` (GGUF, e.g. `qwen2-1.5b-q4_k_m.gguf`) loaded via `llama.cpp`'s `llama-cli` binary.
  - All generation and rewriting happens locally on the phone's CPU/GPU.
  - No HTTP endpoints, no OpenAI‑style APIs, no external model servers.

- **Meta‑cognitive core (MetaCognitiveCore)**
  - Orchestrates language, memory, tools, and retrieval.
  - Centralizes decision‑making for:
    - Knowledge lookup and caching
    - Price and weather tools
    - User corrections and dispute logging
    - Search behavior tuning

- **Hierarchical Reasoning Machine (HRM)**
  - Classifies user input into structured intents:
    - `CHAT` – general conversation
    - `PLANNING` – multi‑step plan requests
    - `MEMORY_WRITE` / `MEMORY_READ` – store and recall user facts
    - `CORRECTION` – "that's wrong…" style feedback
    - `SEARCH_HINT` – meta‑instructions about how to search
    - `PRICE_QUERY` – "current price of X"
    - `WEATHER_QUERY` – "what is the weather"
  - Emits actions like `TRIGGER_SCOUT`, `VERIFY_AND_UPDATE`, `PRICE_QUERY`, `WEATHER_QUERY`, and `UPDATE_SEARCH_POLICY` that Meta‑Core executes.

- **Multi‑layer memory system**
  - `episodic` – recent conversation history (rolling window).
  - `semantic` – canonical facts like `knowledge_samsung`, with:
    - Human‑readable summary
    - Metadata (source, confidence, URL, correction flags)
    - Simple bag‑of‑words vector for similarity.
  - `preference` – user preferences and facts.
  - `search_policies` – learned rules for how to search/score sources.

- **Knowledge Scout (RAG‑style retrieval)**
  - Uses a small cache + multiple fetchers:
    - `WikipediaFetcher` – stable definitions and background facts.
    - `RSSFetcher` – live tech/crypto/news from curated RSS feeds.
    - `LocalCorpusFetcher` – searches local `.txt` files under `data/corpus/`.
  - Picks the best candidate (with optional policy bias) and stores it into semantic memory.
  - Meta‑Core then calls Qwen to rewrite the raw snippet into a clean answer.

- **Live tools and real‑world grounding**
  - **TimeService**
    - Uses Python `datetime.now()` to attach `as_of_date` and `as_of_time` to live facts for better temporal awareness.
  - **PriceService**
    - Fetches live crypto prices (e.g. Bitcoin) in USD using CoinGecko's public `/simple/price` API.
    - Meta‑Core builds a short factual summary (price + timestamp) and sends it to Qwen for phrasing.
  - **LocationService**
    - Uses `termux-location` (Termux:API) to obtain GPS coordinates on device.
    - Uses OpenStreetMap Nominatim reverse‑geocoding to convert lat/lon into:
      - Human label (town, state, country; often street and house number when available).
  - **WeatherService**
    - Uses Open‑Meteo's free API for `current_weather` at the current GPS location (or a default fallback near Wethersfield, CT).
    - Converts:
      - Temperature from Celsius to Fahrenheit.
      - Wind speed from km/h to miles per hour.
    - Meta‑Core summarizes and Qwen rewrites the weather into a natural English response.

- **User corrections and search behavior learning**
  - **Corrections (`CORRECTION` → `VERIFY_AND_UPDATE`)**
    - Logs disputes to `data/memory/disputes.json` with:
      - User correction text
      - Old semantic summary and metadata
      - New Scout result and source
    - Updates semantic memory summary and metadata, marking entries as `corrected` and `corrected_by_user`.
  - **Search hints (`SEARCH_HINT` → `UPDATE_SEARCH_POLICY`)**
    - Allows instructions like:
      - "From now on when I ask for the current price of something, focus on real numbers and price data, not hype articles."
    - Stored as `search_policies` with:
      - `pattern` (e.g. `"current price of"`)
      - `rules` (e.g. `require_numeric`, `prefer_source: ["local_rss"]`)
    - KnowledgeScout uses these rules to filter and score results, so retrieval strategy itself adapts based on user feedback.

---

## Architecture Overview

- **LanguageSystem**
  - Thin wrapper around the local `llama-cli` binary:
    - Builds command: `llama-cli -m <model> -p <prompt> --n-predict <N> -no-cnv -st --temp <T>`
    - Runs it via `subprocess.Popen` and returns stdout as text.
  - Exposes:
    - `generate(prompt, system_instruction=None)` – general chat.
    - `rewrite_from_sources(question, raw_summary, source_label)` – RAG answer rewriting.
    - `parse_intent(user_input)` – simple rule‑based intent classification.

- **MetaCognitiveCore**
  - Creates and wires:
    - `MemorySystem`
    - `LanguageSystem` (Qwen via llama.cpp)
    - `HierarchicalReasoningMachine`
    - `KnowledgeScout`
    - `PriceService`, `WeatherService`, `LocationService`
  - Single entrypoint: `run_cycle(user_input)`:
    - Gets intent from `LanguageSystem`.
    - Sends intent + memory context through HRM.
    - Executes HRM's action:
      - Plans, memory writes/reads, knowledge lookup, corrections.
      - Live price + weather queries with time and location context.
      - Search policy updates.
    - Logs the turn into episodic memory and returns a final natural‑language response.

---

## Running Adaptheon on Android (Termux)

### Prerequisites

- Android device with sufficient RAM and storage.
- Termux (from F‑Droid) and Termux:API installed.
- GPS and location permission enabled for Termux:API.
- Internet access for:
  - Downloading the Qwen GGUF model.
  - Live price, weather, and reverse‑geocoding APIs.

### 1. Set up Termux environment
pkg update && pkg upgrade -y
pkg install -y git cmake clang make python termux-api
### 2. Clone this repository
cd ~
git clone https://github.com//Adaptheon.git
cd Adaptheon
### 3. Build `llama.cpp` and run Qwen locally
Clone llama.cpp inside Adaptheon
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
Build with CMake
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
This produces `build/bin/llama-cli` which is used by Adaptheon for all LLM calls.

### 4. Download a Qwen GGUF model

From `~/Adaptheon`:
mkdir -p models/qwen
cd models/qwen
Download a compatible model, e.g. `Qwen2-1.5B-Instruct` in GGUF format (q4_k_m) from a model hub.

Example (replace the URL with the actual GGUF link):
wget "https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF/resolve/main/qwen2-1_5b-instruct-q4_k_m.gguf" 
-O qwen2-1.5b-q4_k_m.gguf
You should end up with:
~/Adaptheon/models/qwen/qwen2-1.5b-q4_k_m.gguf
### 5. Test `llama-cli` directly
cd ~/Adaptheon/llama.cpp
./build/bin/llama-cli 
-m ~/Adaptheon/models/qwen/qwen2-1.5b-q4_k_m.gguf 
-p "Hello from Qwen on my phone." 
--n-predict 64 
-no-cnv -st
If you see a coherent response, the local Qwen model is working correctly.

### 6. Run Adaptheon

From `~/Adaptheon`:
python main.py
You should see logs like:
[SYSTEM] Booting Adaptheon Phase 2.0...
[LLM] Using local llama.cpp binary at '.../llama.cpp/build/bin/llama-cli' with model '.../models/qwen/qwen2-1.5b-q4_k_m.gguf'
[Scout] Initializing fetcher layers...
[SYSTEM] All Cognitive Modules Online.
Adaptheon Phase 2.0 is listening. Type 'quit' to exit.
Then you can try:
what is samsung
what is the current price of bitcoin
what is the weather
from now on when i ask for the current price of something, focus on real numbers and price data, not hype articles.
that's wrong, samsung is actually an electronics company based in korea...
---

## Roadmap

Planned improvements include:

- Richer corrective‑RAG behavior for facts and numeric queries.
- More specialized fetchers (e.g. political/news briefings, finance summaries).
- Better semantic similarity for related topics and curated local corpora.
- More flexible, model‑driven parsing of `SEARCH_HINT` instructions.

---

## License

This project is for experimental and educational use. Respect the licenses and usage policies of all external tools and services used (llama.cpp, Qwen models, CoinGecko API, Open‑Meteo, Nominatim / OpenStreetMap, etc.).
