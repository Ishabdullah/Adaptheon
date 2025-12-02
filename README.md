# Adaptheon

Minimal core for on-device adaptive reasoning and memory, designed for ultra-low latency mobile execution.

This repository was set up entirely via Termux on an S24 Ultra.

## Mobile / Android Integration

This repo contains the Adaptheon core:
- Hierarchical Reasoning Machine (HRM)
- Knowledge Scout (web/RSS/Wikipedia ingestion)
- Memory system (episodic + semantic + tiny semantic vectors)
- Language interface abstraction

The Android app will sit on top of this core as a separate UI layer:
- Either by calling this core via a local API (Termux/backend style)
- Or by re-implementing the same architecture in Kotlin with the same data layout.

