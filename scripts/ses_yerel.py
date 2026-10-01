#!/usr/bin/env python3
"""Yerel faster-whisper ile ses dosyasini Turkce metne cevir."""
import sys
from faster_whisper import WhisperModel

AUDIO = sys.argv[1] if len(sys.argv) > 1 else "/home/hermes/.hermes/cache/audio/audio_bcfca0c18016.ogg"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "small"

print(f"model yukleniyor: {MODEL} (ilk seferde indirir)")
model = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=6)

print("ceviriliyor...")
segments, info = model.transcribe(
    AUDIO, language="tr", beam_size=5, vad_filter=True,
    condition_on_previous_text=False,
)
print(f"algilanan dil: {info.language} (guven {info.language_probability:.2f}) | sure: {info.duration:.1f} sn")

print("\n=== SESLI MESAJIN METNI ===\n")
parts = []
for seg in segments:
    parts.append(seg.text.strip())
    print(seg.text.strip())

full = " ".join(parts).strip()
print(f"\n=== BIRLESIK ===\n{full}")
