# Video Studio

Workspace for video, motion graphics and voiceover. Skills live in `.claude/skills`
(Remotion: `remotion-*`; HyperFrames: `hyperframes*`, `media-use`, `slideshow`, `figma`).

- New container? Run `scripts/setup.sh` first (node_modules and .venv are not committed).
- HyperFrames projects go in `projects/<name>/` (`npx hyperframes init projects/<name>`).
  jsdelivr is blocked in this environment: copy `assets/vendor/gsap.min.js` into the project
  and reference it locally instead of the CDN URL.
- Remotion compositions live in `remotion/src`; render with `npx remotion render <Id> out/<file>.mp4`.
  `remotion.config.ts` points at the preinstalled headless shell because remotion.media is blocked.
- Voiceover: `.venv/bin/python scripts/vo.py "text" -o out/vo.wav [--voice ref.wav] [--model turbo|multilingual]`.
  Chatterbox runs on CPU here (no GPU) - expect slower-than-realtime generation.
  Its weights come from huggingface.co, which must be allowed in the environment's network settings.
- SFX: `assets/sfx/kenney/*` (CC0 Kenney packs, .ogg) and `assets/sfx/motion/*` (original
  ffmpeg-synthesized whooshes, risers, impacts, pops; regenerate with `scripts/make_motion_sfx.sh`).
  Copy the files a project uses into that project so renders stay self-contained.
- Stock media: `scripts/stock.py unsplash photo "<query>"`, `scripts/stock.py pixabay photo|video "<query>"`
  (`--search-only` to list, `-n`, `--orientation landscape|vertical`). Needs `UNSPLASH_ACCESS_KEY` /
  `PIXABAY_API_KEY` env vars and api.unsplash.com, images.unsplash.com, pixabay.com, cdn.pixabay.com allowed.
  Downloads go to `assets/stock/<source>/<type>/` with `credits.json`; credit Unsplash photographers
  ("Photo by X on Unsplash") in the video description.
