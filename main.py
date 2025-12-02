#!/usr/bin/env python3
import sys
import os

# Ensure we can import from src
sys.path.append(os.path.join(os.getcwd(), "src"))

from meta_core import MetaCognitiveCore

if __name__ == "__main__":
    # In Phase 1, we run the Meta Core directly
    MetaCognitiveCore().run_cycle("System Check") # Warmup
    os.system("python src/meta_core.py")
