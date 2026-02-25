import os
import sys
import torch
import ollama
import sounddevice as sd
from kokoro import KPipeline
from faster_whisper import WhisperModel

# --- 1. SET PATHS ---
os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"
os.environ["PHONEMIZER_ESPEAK_PATH"] = r"C:\Program Files\eSpeak NG"

def check_system():
    print("\n--- JARVIS INSTALLATION CHECK ---")

    # [1/4] Python Version
    print(f"[1/4] Python Version: {sys.version.split()[0]}")

    # [2/4] Ollama (Brain)
    try:
        # We use a simple call to see if the service is alive
        response = ollama.list()
        # NEW SYNTAX for 2026 version: response.models is a list of objects
        model_names = [m.model for m in response.models]
        print(f"[2/4] Ollama: Connected. Found models: {model_names}")
    except Exception as e:
        print(f"[2/4] Ollama: FAILED. Error: {e}")

    # [3/4] Faster-Whisper (Ears)
    try:
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("[3/4] Faster-Whisper: Ready.")
    except Exception as e:
        print(f"[3/4] Faster-Whisper: FAILED. Error: {e}")

    # [4/4] Kokoro (Voice)
    try:
        pipeline = KPipeline(lang_code='a')
        print("[4/4] Kokoro TTS: Ready. Playing test audio...")
        generator = pipeline("System check complete. All modules are green.", voice='af_nicole', speed=1)
        for _, _, audio in generator:
            sd.play(audio, 24000)
            sd.wait()
    except Exception as e:
        print(f"[4/4] Kokoro TTS: FAILED. Error: {e}")

# IMPORTANT: This line MUST be at the very bottom and NOT indented
if __name__ == "__main__":
    check_system()