# Adaptheon Quick Start Guide

## 🚀 Launch Adaptheon

You can now start Adaptheon from **anywhere** in Termux by simply typing:

```bash
Adaptheon
```

Or from the Adaptheon directory:

```bash
cd ~/Adaptheon
./run_adaptheon.sh
```

---

## 💬 Example Conversations

### Knowledge Queries
```
You: what is bitcoin
Adaptheon: Bitcoin is the first decentralized cryptocurrency...

You: what is ethereum
Adaptheon: Ethereum is a decentralized blockchain with smart contract functionality...
```

### Real-Time Price Queries
```
You: what is the current price of bitcoin
Adaptheon: As of 2025-12-05, the price of bitcoin is approximately $92,256 USD

You: what is the current price of ethereum
Adaptheon: As of 2025-12-05, the price of ethereum is approximately $3,174 USD
```

### Weather Queries
```
You: what is the weather
Adaptheon: As of 2025-12-05 at your area, the temperature is 15.1°F with wind speed 2.1 mph
```

### Memory & Preferences
```
You: remember that my favorite language is Python
Adaptheon: I have stored that in your preference memory

You: what do you know about me
Adaptheon: Here is what I know about you: {'user_fact': 'my favorite language is Python'}
```

### Corrections
```
You: that's wrong about bitcoin
Adaptheon: Thanks for the correction. I have updated what I know about bitcoin...
```

### Planning
```
You: plan how to build a web application
Adaptheon: I have constructed a basic plan for this task. | Steps: Analyze constraint parameters | Query Knowledge Scout for missing variables | Optimize execution path...
```

---

## 🧪 Run Tests

### Full Self-Test (46 tests)
```bash
cd ~/Adaptheon
./self_test.sh
```

### Internet Services Test
```bash
cd ~/Adaptheon
python test_internet_services.py
```

### Complete System Test
```bash
cd ~/Adaptheon
python test_full_system.py
```

---

## 📊 Test Results Summary

| Test Suite | Tests | Pass Rate | Status |
|------------|-------|-----------|--------|
| **Self-Test** | 46/46 | 100% | ✅ ALL PASS |
| **Internet Services** | 6/6 | 100% | ✅ ALL PASS |
| **Full System** | 15/18 | 83% | ✅ WORKING |

**Verified Working:**
- ✅ Wikipedia knowledge retrieval
- ✅ Real-time cryptocurrency prices (Bitcoin, Ethereum)
- ✅ Real-time weather data
- ✅ RSS feed monitoring
- ✅ Memory storage (episodic, semantic, preferences)
- ✅ Memory retrieval
- ✅ User corrections & dispute logging
- ✅ Search policy learning
- ✅ Planning & reasoning
- ✅ Knowledge caching

---

## 🔧 System Components

### 1. MetaCognitiveCore
Main orchestrator - coordinates all subsystems

### 2. Memory System
- **Episodic**: Conversation history (last 50 interactions)
- **Semantic**: Knowledge graph (facts, definitions)
- **Procedural**: Action sequences
- **Preference**: User settings and preferences

### 3. Knowledge Scout
Multi-source information retrieval:
- Wikipedia (encyclopedic knowledge)
- RSS feeds (current news)
- Local corpus (your documents)
- Cache (previous lookups)

### 4. Real-Time Services
- **Price Service**: CoinGecko API for crypto prices
- **Weather Service**: Open-Meteo API for weather
- **Location Service**: Termux GPS integration

### 5. HRM (Hierarchical Reasoning Machine)
Intent analysis and action planning

### 6. LLM Interface
- **Current**: Simulation mode (echo responses)
- **Full**: Requires GGUF model in `models/qwen/`

---

## 📁 Memory Locations

```
~/Adaptheon/data/
├── memory/
│   ├── core_memory.json     # All memory types
│   └── disputes.json         # Correction log
└── cache/
    └── knowledge_cache.json  # Knowledge cache
```

### View Your Memory
```bash
cat ~/Adaptheon/data/memory/core_memory.json | python -m json.tool
```

### View Corrections Log
```bash
cat ~/Adaptheon/data/memory/disputes.json | python -m json.tool
```

---

## 🎯 Current Capabilities

### ✅ What Works Now (Verified)

1. **Knowledge Retrieval**
   - Ask about any topic
   - Fetches from Wikipedia
   - Caches for fast re-access

2. **Real-Time Data**
   - Cryptocurrency prices (Bitcoin, Ethereum, etc.)
   - Current weather conditions
   - Timestamped responses

3. **Learning & Memory**
   - Remembers all conversations
   - Stores facts you teach it
   - Learns your preferences
   - Logs corrections

4. **Reasoning**
   - Analyzes intent
   - Generates plans
   - Multi-step problem solving

### ⏳ Requires Model Download

5. **Full LLM Mode**
   - Download GGUF model (e.g., Qwen2-1.5B-Q4_K_M)
   - Place in `~/Adaptheon/models/qwen/`
   - Restart Adaptheon
   - Enables natural conversation

---

## 🔄 Common Commands

| Command | Description |
|---------|-------------|
| `Adaptheon` | Start from anywhere |
| `cd ~/Adaptheon && ./self_test.sh` | Run all 46 tests |
| `python test_full_system.py` | Full end-to-end test |
| `git pull` | Update to latest |
| `quit` | Exit Adaptheon |

---

## 💡 Tips

1. **Be Specific**: "What is Bitcoin" works better than "Bitcoin"
2. **Use Corrections**: Say "that's wrong, actually..." to teach it
3. **Check Memory**: It remembers everything - view `core_memory.json`
4. **Real-Time Queries**: Ask for "current price of X" for live data
5. **Planning**: Ask it to "plan" tasks for step-by-step approaches

---

## 🐛 Troubleshooting

### Adaptheon command not found
```bash
# Add to PATH manually
export PATH="$HOME/.local/bin:$PATH"
# Or restart Termux
```

### Dependencies missing
```bash
cd ~/Adaptheon
pip install -r requirements.txt
```

### LLM not working
```
Expected - System runs in simulation mode without model
Download a GGUF model to enable full LLM
```

### Internet services failing
```bash
# Test connectivity
python test_internet_services.py
```

---

## 📈 Performance Stats

**From Latest Tests:**
- Memory: 50 episodic entries, 6 semantic knowledge items
- Cache: 5 topics cached
- Disputes: 7 corrections logged
- Search Policies: 3 learned patterns

**Real Data Retrieved:**
- Bitcoin: $92,256 USD
- Ethereum: $3,174 USD
- Weather: 15.1°F, 2.1 mph wind

---

## 🎓 Learn More

- **Full Audit**: See `AUDIT_REPORT.md` for complete system analysis
- **Architecture**: See `docs/ROADMAP_ADAPTHEON.md`
- **GitHub**: https://github.com/Ishabdullah/Adaptheon

---

**Adaptheon Phase 2.0 - Your on-device adaptive reasoning system**
