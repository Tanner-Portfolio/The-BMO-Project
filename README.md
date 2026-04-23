# The BMO Project: Edge AI Assistant

## 📝 Project Overview
The BMO Project is a localized, edge-computing AI assistant built on a Raspberry Pi 5. Inspired by BMO from *Adventure Time*, this project combines hardware engineering, local Large Language Model (LLM) processing, and custom audio-pipeline scripting to create an autonomous, interactive assistant capable of localized reasoning, game emulation, and voice interaction.

## 🏗️ Technical Architecture
*   **Hardware:** Raspberry Pi 5 (acting as the edge-compute node).
*   **Compute Processing:** Localized AI inference avoiding reliance on cloud-based APIs for enhanced privacy and latency reduction.
*   **Audio Pipeline:** Custom wake-word detection logic integrated with voice activity detection (VAD).

## 🛠️ Tools Used
*   **Hardware:** Raspberry Pi 5, external microphone/speaker peripherals.
*   **Languages:** Python, Bash.
*   **Libraries/Frameworks:** *fill this in with scripts - remember PyAudio, Whisper, Ollama]*

## 🚀 Key Features & Development Status
*   **Continuous Listening & Wake Word:** Transitioned from manual execution to an automated, continuous listening loop. Wake word logic is currently in the tuning phase.
*   **Game Emulation:** Architecture designed to execute and interact with localized game environments.
*   **Personality Integration:** Prompt engineering tailored to replicate specific personality constraints dynamically.
