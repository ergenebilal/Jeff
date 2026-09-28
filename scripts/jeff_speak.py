#!/usr/bin/env python3.11
"""
Jeff Speak — Kokoro TTS with the Jeff voice (am_liam).

Usage:
    jeff_speak.py "Your Turkish text here"             → outputs to stdout (wav)
    jeff_speak.py "Text" /path/to/output.mp3           → outputs to mp3 file
    jeff_speak.py --mp3 "Text"                         → outputs to ./output.mp3
    jeff_speak.py --wav "Text"                         → outputs to ./output.wav
    echo "Text" | jeff_speak.py                        → reads from stdin, writes to stdout (wav)

If no output path is given and not piping, writes to ./output.mp3 by default.
"""

import argparse
import io
import sys
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from pykokoro import build_pipeline, PipelineConfig, GenerationConfig


# ── Jeff voice config ──────────────────────────────────────────────────────────
VOICE = "am_liam"
LANG = "en-us"
SPEED = 1.0          # natural pace
MODEL_SOURCE = "huggingface"
MODEL_VARIANT = "v1.0"
PROVIDER = "cpu"

# ── Lazy singleton pipeline (created once, reused across calls) ────────────────
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline(
            config=PipelineConfig(
                voice=VOICE,
                generation=GenerationConfig(lang=LANG, speed=SPEED),
                model_source=MODEL_SOURCE,
                model_variant=MODEL_VARIANT,
                provider=PROVIDER,
            ),
            eager=True,
        )
    return _pipeline


def synthesize(text: str) -> tuple[np.ndarray, int]:
    """Return (audio_array, sample_rate) for the given text."""
    pipe = _get_pipeline()
    result = pipe.run(text)
    return result.audio, result.sample_rate


def write_wav(audio: np.ndarray, sample_rate: int, path: str | Path) -> None:
    """Write raw audio array to a WAV file (no extra dependencies)."""
    sf.write(str(path), audio, sample_rate)


def write_mp3(audio: np.ndarray, sample_rate: int, path: str | Path) -> None:
    """Write audio to MP3 via sox/ffmpeg if available, otherwise fallback to WAV."""
    path = Path(path)
    # Write a temp WAV first
    temp_wav = path.with_suffix(".wav")
    write_wav(audio, sample_rate, temp_wav)

    # Try ffmpeg → mp3
    import subprocess
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(temp_wav), "-codec:a", "libmp3lame", "-q:a", "2", str(path)],
            capture_output=True, check=True,
        )
        temp_wav.unlink(missing_ok=True)  # clean up temp
    except (FileNotFoundError, subprocess.CalledProcessError):
        # No ffmpeg — rename WAV to requested name
        if path.suffix == ".mp3":
            # Keep the wav, just rename it (user gets wav despite asking for mp3)
            temp_wav.rename(path.with_suffix(".wav"))
            print("Warning: ffmpeg not found; wrote WAV instead of MP3.", file=sys.stderr)
        else:
            temp_wav.rename(path)


def main():
    parser = argparse.ArgumentParser(description="Jeff speaks Turkish (and anything else).")
    parser.add_argument("text", nargs="?",
                        help="Text to speak. Reads from stdin if not provided.")
    parser.add_argument("output", nargs="?",
                        help="Output file (.wav or .mp3). Default: ./output.mp3")
    parser.add_argument("--mp3", action="store_true",
                        help="Output as MP3 (default).")
    parser.add_argument("--wav", action="store_true",
                        help="Output as WAV.")
    args = parser.parse_args()

    # ── Get text ───────────────────────────────────────────────────────────────
    if args.text:
        text = args.text
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("Error: provide text as argument or pipe it via stdin.", file=sys.stderr)
        sys.exit(1)

    if not text:
        print("Error: empty text.", file=sys.stderr)
        sys.exit(1)

    # ── Synthesize ─────────────────────────────────────────────────────────────
    try:
        audio, sr = synthesize(text)
    except Exception as e:
        print(f"Error: synthesis failed — {e}", file=sys.stderr)
        sys.exit(1)

    # ── Output ──────────────────────────────────────────────────────────────────
    output_path = args.output
    use_mp3 = args.mp3 or (output_path and output_path.endswith(".mp3")) or (not args.wav)

    if output_path:
        if output_path.endswith(".mp3") or (use_mp3 and not output_path.endswith(".wav")):
            write_mp3(audio, sr, output_path)
        else:
            write_wav(audio, sr, output_path)
        print(f"✓ Saved to {output_path}", file=sys.stderr)
    else:
        # Default: write to ./output.mp3 (or output.wav if --wav)
        default_name = "output.mp3" if use_mp3 else "output.wav"
        out = Path(default_name)
        if use_mp3:
            write_mp3(audio, sr, out)
        else:
            write_wav(audio, sr, out)
        print(f"✓ Saved to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
