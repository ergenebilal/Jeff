#!/usr/bin/env python3.11
"""Jeff'in sesiyle konuş - XTTS v2 + Finch dublaj"""
import sys, os
from TTS.api import TTS

SPEAKER_WAV = os.path.expanduser("~/.hermes/jeff_sesi.wav")

def main():
    if len(sys.argv) < 2:
        print("Kullanım: jeff_konus.py <metin> [output.wav]")
        sys.exit(1)
    
    text = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "/tmp/jeff_konus.wav"
    
    os.environ["COQUI_TOS_AGREED"] = "1"
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    tts.tts_to_file(text=text, speaker_wav=SPEAKER_WAV, language="tr", file_path=output)
    print(f"Ses kaydedildi: {output}")
    print(f"Boyut: {os.path.getsize(output)/1024:.0f} KB")

if __name__ == "__main__":
    main()
