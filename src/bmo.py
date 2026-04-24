import os
import time
import json
import threading
import subprocess
import requests
import pygame
import numpy as np
import sounddevice as sd
import re
from PIL import Image
from faster_whisper import WhisperModel
from vosk import Model, KaldiRecognizer
import queue

# --- CONFIG ---
FACES_DIR = "/home/bmo/assets/faces" # File location for BMO's facial expressions
OLLAMA_URL = "http://localhost:11434/api/generate" # Local API reference for OLLAMA
PIPER_EXE = "/home/bmo/piper/piper" # piper reference
PIPER_MODEL = "/home/bmo/models/bmo.onnx" # BMO voice .onnx file here
VOSK_MODEL_PATH = "/home/bmo/models/vosk_model" # vosk model 


#Emotion map for BMO linked with relevant face expressions
EMOTION_MAP = {
    "neutral": "bmo_face_01", "happy": "bmo_face_2", "content": "bmo_face_3",
    "frown": "bmo_face_4", "excited": "bmo_face_5", "sad": "bmo_face_6",
    "amazed": "bmo_face_23", "confused": "bmo_face_24"
} 

# --- ENGINE ---
print("BMO is warming up his internal brain...")
whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
vosk_model = Model(VOSK_MODEL_PATH)
audio_queue = queue.Queue(maxsize=20)

# --- GLOBAL STATE ---
# Set default face
current_face = "bmo_face_01"
is_thinking = False
interaction_active = threading.Event()
stop_blinking = threading.Event()
follow_up_mode = False 
chat_history = []

def load_faces():
    cache = {}
    for filename in os.listdir(FACES_DIR):
        if filename.endswith(".png"):
            path = os.path.join(FACES_DIR, filename)
            img = Image.open(path).convert("RGB").resize((800, 480))
            cache[filename.replace(".png", "")] = pygame.transform.rotate(pygame_img := pygame.image.fromstring(img.tobytes(), img.size, "RGB"), 90)
    return cache

def thinking_blink_loop():
    global current_face
    while not stop_blinking.is_set():
        current_face = "bmo_face_01"
        time.sleep(0.4)
        if stop_blinking.is_set(): break
        current_face = "bmo_face_3" 
        time.sleep(0.15)

def bmo_speak(text):
    # Remove any accidental mentions of 'bmo_face_XX' from speech
    clean_text = re.sub(r'bmo_face_\d+', '', text).strip()
    if not clean_text: clean_text = "Yay!"

    wav_path = "/tmp/speech.wav"
    if os.path.exists(wav_path): os.remove(wav_path)
    with open("/tmp/bmo_text.txt", "w") as f: f.write(clean_text)
    
    # Piper generation
    subprocess.run(f'cat /tmp/bmo_text.txt | {PIPER_EXE} --model {PIPER_MODEL} --length_scale 1.15 --output_file {wav_path}', shell=True)
    subprocess.run(["aplay", "-D", "plughw:0,0", "-q", wav_path])

def call_ollama(prompt):
    global chat_history
    # Message for the AI model to act like BMO.
    system_intro = (
        "You are BMO. You are a real boy! You are innocent, childlike, and sincere. "
        "Do not use slang like 'kid', 'bro', or 'mate'. Use words like 'Yay' and 'Boop'. "
        "Keep it under 10 words. NEVER mention filenames like 'bmo_face'. "
        "Respond ONLY in JSON: {'speech': '...', 'emotion': 'happy/sad/excited/amazed/confused'}"
    )
    context = "\n".join(chat_history[-3:]) 
    payload = {
        "model": "bmo:latest",
        "prompt": f"{system_intro}\nContext:\n{context}\nUser: {prompt}",
        "stream": False, "format": "json"
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=25)
        raw_content = r.json()['response']
        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("speech", "Neato!"), data.get("emotion", "happy")
        return raw_content.strip(), "happy"
    except:
        return "I am thinking so hard!", "content"

def bmo_interaction_logic(is_followup=False):
    global current_face, is_thinking, follow_up_mode, chat_history
    is_thinking = True
    stop_blinking.clear()
    threading.Thread(target=thinking_blink_loop, daemon=True).start()
    
    try:
        if not is_followup:
            subprocess.run(["aplay", "-D", "plughw:0,0", "-q", "/home/bmo/assets/sounds/hmm.wav"])

        print("BMO is listening...")
        cmd_file = "/tmp/cmd.wav"
        if os.path.exists(cmd_file): os.remove(cmd_file)
        subprocess.run(["arecord", "-D", "plughw:0,0", "-f", "S16_LE", "-r", "16000", "-d", "4", cmd_file])

        if os.path.exists(cmd_file):
            segments, _ = whisper_model.transcribe(cmd_file)
            user_text = " ".join([s.text for s in segments]).strip().lower()
            
            if user_text and len(user_text) > 1:
                print(f"You: {user_text}")
                chat_history.append(f"User: {user_text}")
                
                speech, emotion = call_ollama(user_text)
                
                # Update Face BEFORE speaking
                stop_blinking.set() 
                current_face = EMOTION_MAP.get(emotion.lower(), "bmo_face_01")
                
                print(f"BMO [{emotion}]: {speech}")
                chat_history.append(f"BMO: {speech}")
                bmo_speak(speech)
                follow_up_mode = True 
            else:
                follow_up_mode = False
    finally:
        stop_blinking.set()
        current_face = "bmo_face_01"
        is_thinking = False
        while not audio_queue.empty(): audio_queue.get_nowait()
        interaction_active.clear()
def audio_callback(indata, frames, time, status):
    # Pass raw audio to queue
    if not is_thinking:
        audio_queue.put(bytes((indata * 32767).astype(np.int16)[::3]))

def vosk_worker():
    global follow_up_mode
    # Broad grammar to catch all variations of BMO's name
    grammar = '["bmo", "be mo", "bee mo", "hey bmo", "hey bee mo", "be more", "[unk]"]'
    rec = KaldiRecognizer(vosk_model, 16000, grammar)
    
    while True:
        if interaction_active.is_set():
            time.sleep(0.2)
            continue
            
        try:
            # Clear old audio so he doesn't "hallucinate" wake words from the past
            while not audio_queue.empty(): audio_queue.get_nowait()
            
            with sd.InputStream(device=0, samplerate=48000, channels=1, dtype='float32', callback=audio_callback):
                start_time = time.time()
                print("BMO Ears: Active.")
                while not interaction_active.is_set():
                    # Follow-up logic
                    if follow_up_mode:
                        if time.time() - start_time > 10:
                            follow_up_mode = False
                            print("BMO is going to sleep...")
                            break
                        
                        # In follow-up mode, trigger on ANY detected speech
                        if not audio_queue.empty():
                            data = audio_queue.get()
                            if rec.AcceptWaveform(data):
                                interaction_active.set()
                                break
                    else:
                        # Normal mode: Only trigger on "BMO"
                        data = audio_queue.get()
                        if rec.AcceptWaveform(data):
                            res = json.loads(rec.Result())
                            if any(name in res.get("text", "") for name in ["bmo", "be mo", "bee mo", "be more"]):
                                interaction_active.set()
                                break
                        # Check partial result for faster wake logic
                        partial = json.loads(rec.PartialResult()).get("partial", "")
                        if any(name in partial for name in ["bmo", "be mo"]):
                            interaction_active.set()
                            break

            if interaction_active.is_set():
                time.sleep(0.3) # Release hardware
                bmo_interaction_logic(is_followup=follow_up_mode)
        except Exception as e:
            print(f"Mic Error: {e}")
            time.sleep(1)

def main():
    global current_face
    os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
    pygame.display.init()
    screen = pygame.display.set_mode((480, 800), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    face_cache = load_faces()
    
    threading.Thread(target=vosk_worker, daemon=True).start()
    
    print("BMO 3.5 (Harmony) is online!")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.FINGERDOWN and not is_thinking:
                follow_up_mode = False
                interaction_active.set()
        
        face_img = face_cache.get(current_face, face_cache["bmo_face_01"])
        screen.blit(face_img, (0, 0))
        pygame.display.flip()
        time.sleep(0.05)

if __name__ == "__main__":
    main()
