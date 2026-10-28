#!/usr/bin/env bash
# Synthesize original motion-graphics SFX with ffmpeg (no licensing concerns).
# Usage: scripts/make_motion_sfx.sh [outdir]
set -euo pipefail
OUT="${1:-assets/sfx/motion}"; mkdir -p "$OUT"
SR=48000
f() { ffmpeg -hide_banner -loglevel error -y "$@"; }

# Whooshes: filtered noise with a bandpass sweep and a swell envelope
for i in 1 2 3; do
  d=$(echo "0.45 0.6 0.8" | cut -d' ' -f$i); c=$(echo "900 1400 600" | cut -d' ' -f$i)
  f -f lavfi -i "anoisesrc=d=$d:c=pink:r=$SR:a=0.9" \
    -af "bandpass=f=$c:width_type=o:w=1.6,vibrato=f=6:d=0.3,afade=t=in:d=$(echo "$d*0.55"|bc -l|sed "s/^\./0./"),afade=t=out:st=$(echo "$d*0.55"|bc -l|sed "s/^\./0./"):d=$(echo "$d*0.45"|bc -l|sed "s/^\./0./"),loudnorm=I=-18:TP=-1.5" "$OUT/whoosh-$i.wav"
done
# Swish (short, bright)
f -f lavfi -i "anoisesrc=d=0.25:c=white:r=$SR" -af "highpass=f=2500,afade=t=in:d=0.08,afade=t=out:st=0.08:d=0.17,loudnorm=I=-20:TP=-1.5" "$OUT/swish.wav"
# Riser: rising sine + noise build
f -f lavfi -i "aevalsrc='0.4*sin(2*PI*(200*t+300*t*t/2))+0.15*(random(0)-0.5)*t/2':d=2:s=$SR" -af "afade=t=in:d=1.8,highpass=f=120,loudnorm=I=-18:TP=-1.5" "$OUT/riser.wav"
# Reverse whoosh into hit
f -f lavfi -i "anoisesrc=d=1.2:c=pink:r=$SR" -af "lowpass=f=3000,afade=t=in:d=1.15,afade=t=out:st=1.15:d=0.05,loudnorm=I=-18:TP=-1.5" "$OUT/reverse-swell.wav"
# Impact / boom: pitch-dropping sine with fast decay
f -f lavfi -i "aevalsrc='sin(2*PI*(90*t-60*t*t))*exp(-5*t)+0.3*(random(0)-0.5)*exp(-30*t)':d=1.2:s=$SR" -af "lowpass=f=4000,loudnorm=I=-16:TP=-1" "$OUT/impact.wav"
# Sub drop
f -f lavfi -i "aevalsrc='sin(2*PI*(70*t-25*t*t))*exp(-2*t)':d=1.6:s=$SR" -af "loudnorm=I=-16:TP=-1" "$OUT/sub-drop.wav"
# Pop (UI element appears)
f -f lavfi -i "aevalsrc='sin(2*PI*(500*t+4000*t*t))*exp(-40*t)':d=0.12:s=$SR" -af "loudnorm=I=-20:TP=-1.5" "$OUT/pop.wav"
# Tick (counter/clock)
f -f lavfi -i "aevalsrc='sin(2*PI*2200*t)*exp(-120*t)':d=0.05:s=$SR" -af "loudnorm=I=-24:TP=-2" "$OUT/tick.wav"
# Ding (notification)
f -f lavfi -i "aevalsrc='(0.6*sin(2*PI*1320*t)+0.3*sin(2*PI*2640*t)+0.1*sin(2*PI*3960*t))*exp(-4*t)':d=1:s=$SR" -af "loudnorm=I=-20:TP=-1.5" "$OUT/ding.wav"
# Glitch: bitcrushed stutter
f -f lavfi -i "aevalsrc='0.6*(2*gte(sin(2*PI*180*t),0)-1)*gt(random(0),0.4)':d=0.35:s=$SR" -af "acrusher=bits=4:samples=12,afade=t=out:st=0.25:d=0.1,loudnorm=I=-20:TP=-1.5" "$OUT/glitch.wav"
# Keyboard typing burst
f -f lavfi -i "aevalsrc='(random(0)-0.5)*exp(-200*mod(t,0.085))':d=1:s=$SR" -af "highpass=f=1500,loudnorm=I=-24:TP=-2" "$OUT/typing.wav"
# Camera shutter
f -f lavfi -i "aevalsrc='(random(0)-0.5)*(exp(-90*t)+exp(-90*abs(t-0.07))*gt(t,0.07))':d=0.2:s=$SR" -af "bandpass=f=3000:w=4000,loudnorm=I=-20:TP=-1.5" "$OUT/shutter.wav"
echo "Wrote $(ls "$OUT" | wc -l) files to $OUT"
