#!/usr/bin/env bash
# Rebuild the video-studio toolchain in a fresh container. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Node packages (Remotion, HyperFrames, GSAP)"
npm install --no-audit --no-fund

echo "== Python 3.11 venv: Chatterbox TTS, Kokoro, Whisper"
[ -x .venv/bin/python ] || uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt

echo "== HyperFrames headless Chrome"
npx hyperframes browser ensure || echo "warn: browser download failed (network policy?)"

echo "== Motion SFX"
[ -n "$(ls assets/sfx/motion 2>/dev/null)" ] || scripts/make_motion_sfx.sh

echo "== Chatterbox weights (needs huggingface.co allowed)"
.venv/bin/python -c "from chatterbox.tts import ChatterboxTTS; ChatterboxTTS.from_pretrained(device='cpu')" \
  || echo "warn: could not fetch Chatterbox weights - allow huggingface.co in the environment's network settings"
echo "done"
