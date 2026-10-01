#!/usr/bin/env python3
"""Yerel faster-whisper ile ses dosyasini Turkce metne cevir (VAD olmadan, tam kayit)."""
import sys
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio

AUDIO = sys.argv[1] if len(sys.argv) > 1 else "/home/hermes/.hermes/cache/audio/audio_bcfca0c18016.ogg"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "small"

# Gercek sure (VAD'in ne kadar kestigini gormek icin)
audio = decode_audio(AUDIO, sampling_rate=16000)
print(f"gercek ses suresi: {len(audio)/16000:.1f} saniye")

model = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=6)
print(f"model: {MODEL} | ceviriliyor (VAD kapali)...")

segments, info = model.transcribe(
    AUDIO, language="tr", beam_size=5,
    vad_filter=False,                  # sesi KESME
    condition_on_previous_text=False,
    no_speech_threshold=None,
)
print(f"algilanan dil: {info.language} (guven {info.language_probability:.2f})")

print("\n=== SESLI MESAJIN METNI ===\n")
parts = []
for seg in segments:
    t = seg.text.strip()
    if t:
        parts.append(t)
        print(f"[{seg.start:6.1f}s] {t}")

full = " ".join(parts).strip()
print(f"\n=== BIRLESIK METIN ===\n{full}")
