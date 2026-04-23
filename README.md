# Project BMO: Autonomous Edge AI

## 📝 Project Overview
**Project BMO** is an autonomous, 100% offline, locally-hosted entity based on the character BMO from *Adventure Time*. 

This project goes beyond API wrappers/cloud-based LLMs to create a true iteration of BMO. It features a custom-trained Llama-3 personality, a natively cloned neural TTS voice, local vision, and an agentic logic loop running entirely on a **Raspberry Pi 5**.

## 🏗️ Technical Architecture
*   **Compute:** Raspberry Pi 5 (8GB RAM), Debian Trixie (Kernel 6.12).
*   **Brain (LLM):** Llama-3-8B-Instruct (Fine-tuned via Unsloth/QLoRA), deployed via Ollama (.gguf Q4_K_M).
*   **Voice (TTS):** Piper TTS ONNX model (Approx. 1300-epochs). 
*   **Ears (STT & Wake Word):** Vosk/OpenWakeWord for continuous listening, Faster-Whisper (tiny.en, int8) for transcription.
*   **Vision (VLM):** Moondream via Ollama, utilizing Raspberry Pi Camera Module 3.
*   **UI/Display:** Pygame running natively via KMSDRM/Wayland (Direct Hardware Rendering).

---

## 🧠 1. The Mind: Personality Extraction & Fine-Tuning
Instead of relying on generic system prompts typical for AI agents, BMO's model weights were fine-tuned using the show's canonical dialogue.
*   **Data Scraping:** Developed a custom Python scraper (BeautifulSoup/MediaWiki API) to extract 845 lines of BMO dialogue from the *Adventure Time* Fandom Wiki, preserving conversational context.
*   **Model Fine-Tuning:** Formatted data into ChatML and utilized Unsloth (RTX 4080 SUPER, 16GB VRAM) to execute a 300-epoch QLoRA fine-tune. This baked BMO's specific syntax ("Yay!", "Boop!") directly into the Llama-3 model.

## 🗣️ 2. The Voice: Audio Isolation & Neural TTS Training
BMO's voice is a custom-trained neural vocoder based entirely on Niki Yang’s original performance.
*   **Vocal Isolation:** Extracted MKV episodes to WAV, utilizing **UVR5 (Ultimate Vocal Remover)** and the MDX-Net model to surgically strip background jazz, ambient noise, and sound effects.
*   **Forced Alignment:** Leveraged **WhisperX** with a custom fuzzy-matching script to compare the scraped text lines against clean audio tracks, automatically generating 306 perfect, timestamped audio snippets.
*   **Voice Training:** Compiled the `monotonic_align` C++ engine from source and trained a custom `.onnx` voice model via Piper TTS for 1300 epochs.

## 👂 3. The Senses: Local STT, Wake Word, & Vision
*   **Hardware Resampling Bridge:** The USB microphone records natively at 48kHz, but the wake-word engine requires 16kHz. Engineered a custom Python `sounddevice` bridge utilizing NumPy decimation (`pcm[::3]`) to downsample audio in real-time, preventing `ALSA Invalid Sample Rate` crashes.
*   **Wake Word & STT:** Utilizes a custom `.tflite` model for 100% offline "Hey BMO" triggering, handing off to `faster-whisper` (CPU-bound) for sub-second transcription.
*   **Computer Vision:** Triggered by keywords ("look" or "see"), `rpicam-still` silently captures the environment, passing the frame to the Moondream (1.6GB) Vision-Language Model to generate in-character descriptions of the physical world.

---

## 🛠️ Overcoming Hardware & Architectural Failures
Building a localized OS on a Raspberry Pi 5 presented significant engineering hurdles:

1.  **The ReSpeaker 2-Mics HAT I2C Failure:**
    *   *Issue:* The Pi 5's new RP1 architecture broke legacy Seeed Studio drivers. Attempts to manually bind the `tlv320aic3104` codec via I2C (`0x18`) and force ALSA dmix bridges resulted in endless `Device or resource busy` loops.
    *   *Resolution:* Pivoted from GPIO I2S audio to a Sabrent USB Audio Adapter. Spliced a traditional headphone driver and integrated a 3.5mm pin-mic. The ReSpeaker HAT was salvaged for a secondary Pi 3 project (Project Jake).
2.  **Pygame Audio Locks & ALSA Conflicts:**
    *   *Issue:* `pygame.init()` spawned a background audio mixer that seized exclusive control of the USB soundcard, locking `arecord` and `aplay`.
    *   *Resolution:* Stripped Pygame initialization down to `pygame.display.init()`. Implemented aggressive `threading.Event()` logic (`stop_listening.set()`) to force the microphone stream to yield hardware control prior to the STT recording phase.
3.  **KMSDRM Direct Rendering (The Face):**
    *   *Issue:* Pygame failed to initialize via SSH on the 4-inch DSI screen due to Wayland compositor conflicts (`kmsdrm not available`).
    *   *Resolution:* Reverted the Pi 5 to X11, enabled Console Autologin, and injected `MESA_LOADER_DRIVER_OVERRIDE=vc4` into the `systemd` service file to force direct hardware rendering for the face UI.

---

## 🚀 Roadmap & Next Steps
*   **Physical Fabrication:** 3D print the "Heart of Gold" internal chassis and teal outer shell using Matte PLA (Bambu Lab A1).
*   **Capacitive Touch:** Integrate TTP223 capacitive touch sensors via GPIO pins to trigger the AI logic loop via physical interactions ("head boops").
*   **Agentic Framework Integration ("OpenClaw"):** Upgrade BMO from a reactive conversationalist to a ReAct logic agent, granting autonomous capabilities to check internal battery levels, manage files, and write/execute self-contained Pygame scripts on his display.
