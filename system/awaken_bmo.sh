#!/bin/bash
# 1. Unmute USB Audio Adapter (Card 0)
amixer -c 0 sset Mic 100% unmute
amixer -c 0 sset Speaker 100% unmute

# 2. Prepare Ollama (Loads BMO into RAM)
# This is to prevent the first interaction from being slow
curl -X POST http://localhost:####/api/generate -d '{"model": "bmo:latest", "keep_alive": -1}'

exit 0
