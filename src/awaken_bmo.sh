#!/bin/bash
# 1. Unmute USB Adapter (Card 0)
amixer -c 0 sset Mic 100% unmute
amixer -c 0 sset Speaker 100% unmute

# 2. Prepare Ollama (Loads BMO model into 8GB RAM)
# This is for ensuring his responses are quick
curl -X POST http://localhost:11434/api/generate -d '{"model": "bmo:latest", "keep_alive": -1}'

exit 0
