# Adaptheon LLM Models Setup

## Model Configuration

Adaptheon uses local GGUF models via llama.cpp for on-device inference with complete privacy.

### Primary Model: Qwen 2 1.5B Instruct
- **Location:** `~/Adaptheon/models/qwen/qwen2-1.5b-q4_k_m.gguf`
- **Size:** 942 MB
- **Quantization:** Q4_K_M (Medium quality, good balance)
- **Source:** [Qwen/Qwen2-1.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF)
- **Performance:** ~16 tokens/second on ARM64 (Termux)
- **Context:** 32,768 tokens

### Fallback Model: Gemma 2 2B Instruct
- **Location:** `~/Adaptheon/models/gemma/gemma-3-1b-instruct.gguf`
- **Size:** 1.6 GB
- **Quantization:** Q4_K_M
- **Source:** [bartowski/gemma-2-2b-it-GGUF](https://huggingface.co/bartowski/gemma-2-2b-it-GGUF)
- **Purpose:** Fallback if Qwen fails or for specialized tasks

## Binary Configuration

### llama.cpp CLI
- **Location:** `~/Adaptheon/llama.cpp/build/bin/llama-cli`
- **Size:** 3.1 MB
- **Build:** Custom ARM64 build with NEON optimizations
- **Commit:** 03d9a77 with Clang 21.1.6 for Android

## Environment Variables

Configuration is stored in `.env`:

```bash
# LLM Model Paths
QWEN_MODEL_PATH=/data/data/com.termux/files/home/Adaptheon/models/qwen/qwen2-1.5b-q4_k_m.gguf
GEMMA_MODEL_PATH=/data/data/com.termux/files/home/Adaptheon/models/gemma/gemma-3-1b-instruct.gguf
LLAMA_BIN_PATH=/data/data/com.termux/files/home/Adaptheon/llama.cpp/build/bin/llama-cli
```

## Verification

Test that models are working:

```bash
cd ~/Adaptheon

# Test llama-cli directly
~/Adaptheon/llama.cpp/build/bin/llama-cli \
  -m ~/Adaptheon/models/qwen/qwen2-1.5b-q4_k_m.gguf \
  -p "Hello" -n 10 --temp 0.7 -no-cnv -st

# Test via Adaptheon
python -c "
import sys
sys.path.append('src')
from components.llm_interface import LanguageSystem
llm = LanguageSystem()
print('LLM Ready:', llm.use_llm)
print(llm.generate('What is 2+2?'))
"

# Test full system
python -c "
import sys
sys.path.append('src')
from meta_core import MetaCognitiveCore
core = MetaCognitiveCore()
print(core.run_cycle('Who are you?'))
"
```

## Model Download (If Needed)

If models are missing, download them:

```bash
cd ~/Adaptheon

# Download Qwen 2 1.5B
cd models/qwen
wget https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF/resolve/main/qwen2-1_5b-instruct-q4_k_m.gguf \
  -O qwen2-1.5b-q4_k_m.gguf

# Download Gemma 2 2B
cd ../gemma
wget https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf \
  -O gemma-3-1b-instruct.gguf
```

## Performance Notes

- **Qwen 2 1.5B** is the primary model due to excellent balance of size/quality
- **Q4_K_M quantization** provides good quality with reasonable size
- **ARM64 NEON** optimizations give ~16 tokens/sec on modern Android devices
- **Memory usage:** ~1.3 GB RAM for Qwen, ~2 GB for Gemma
- **Inference:** Single-turn mode via `-no-cnv -st` flags for reliable subprocess calls

## Troubleshooting

**"Local model or binary not found"**
- Verify paths in `.env` match actual file locations
- Check files exist: `ls -lh ~/Adaptheon/models/qwen/qwen2-1.5b-q4_k_m.gguf`
- Ensure llama-cli is executable: `chmod +x ~/Adaptheon/llama.cpp/build/bin/llama-cli`

**Slow inference**
- Q4_K_M is a good balance; don't use Q8 (too large) or Q2 (poor quality)
- Ensure NEON optimizations compiled (check `system_info` in llama-cli output)
- Close other memory-intensive apps

**Model crashes**
- Reduce context with `-c 2048` flag
- Try smaller batch size: `-b 512`
- Switch to Gemma if Qwen fails

## System Requirements

- **Storage:** 2.5 GB for both models + 500 MB for llama.cpp
- **RAM:** 2 GB free minimum for inference
- **CPU:** ARM64 with NEON (modern Android devices)
- **OS:** Termux on Android or any Linux ARM64 system
