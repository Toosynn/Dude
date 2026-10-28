#!/usr/bin/env python3
"""Generate a voiceover with Chatterbox TTS.

Examples:
  .venv/bin/python scripts/vo.py "Hello world" -o out/vo.wav
  .venv/bin/python scripts/vo.py -f script.txt -o out/vo.wav --voice ref.wav --exaggeration 0.6
  .venv/bin/python scripts/vo.py "Hola" --model multilingual --lang es -o out/hola.wav

Long text is split into sentences, synthesized per chunk and joined with short pauses.
"""
import argparse
import re
import sys

import torch
import torchaudio as ta


def device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def chunks(text, max_chars=280):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    out, cur = [], ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > max_chars:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("text", nargs="?", help="text to speak (or use -f)")
    p.add_argument("-f", "--file", help="read text from a file")
    p.add_argument("-o", "--out", default="vo.wav")
    p.add_argument("--voice", help="reference clip (5-10s WAV) for voice cloning")
    p.add_argument("--model", choices=["english", "turbo", "multilingual"], default="english")
    p.add_argument("--lang", default="en", help="language id for --model multilingual")
    p.add_argument("--exaggeration", type=float, default=0.5, help="emotion intensity, 0.25-2.0")
    p.add_argument("--cfg", type=float, default=0.5, help="pace/guidance; lower = slower, more deliberate")
    p.add_argument("--pause", type=float, default=0.25, help="seconds of silence between chunks")
    a = p.parse_args()

    text = open(a.file).read() if a.file else a.text
    if not text:
        p.error("give text or -f FILE")

    dev = device()
    print(f"loading chatterbox ({a.model}) on {dev}...", file=sys.stderr)
    if a.model == "multilingual":
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS as M
    elif a.model == "turbo":
        from chatterbox.tts_turbo import ChatterboxTurboTTS as M
    else:
        from chatterbox.tts import ChatterboxTTS as M
    model = M.from_pretrained(device=dev)

    kw = {}
    if a.voice:
        kw["audio_prompt_path"] = a.voice
    if a.model != "turbo":
        kw.update(exaggeration=a.exaggeration, cfg_weight=a.cfg)
    if a.model == "multilingual":
        kw["language_id"] = a.lang

    gap = torch.zeros(1, int(model.sr * a.pause))
    parts = []
    for i, c in enumerate(chunks(text)):
        print(f"[{i + 1}] {c}", file=sys.stderr)
        parts += [model.generate(c, **kw).cpu(), gap]
    ta.save(a.out, torch.cat(parts[:-1], dim=1), model.sr)
    print(a.out)


if __name__ == "__main__":
    main()
