#!/usr/bin/env bash
# Owner VM, release 1.6.8 (commit 85c29e7): after drive168d.sh has ended, the walkthrough recorded again in a session
# of its own (vm_walk_168d.sh: the gate's recording failed, see its header), then rendered to MP4 with the project-local
# renderer (render_cast.py: pyte, Pillow, imageio-ffmpeg's ffmpeg, the DejaVu fonts unpacked; nothing installed).
# One heavy job at a time: it waits for drive168d.sh to end.
cd "$HOME/q168d" || exit 1
while pgrep -f "bash drive168d.sh" > /dev/null; do sleep 30; done
echo "== drive168d.sh has ended $(date -u +%H:%M:%SZ)"
grep -q '^\. "\$BASE/walk_helpers.sh" || exit 1$' walkthrough_168.sh || { echo "!! walkthrough_168.sh is not the one that sources the helpers: nothing started"; exit 1; }
ok=1
for st in wprep start build build166 image walk stop after; do
  if [ "$ok" = 0 ] && [ "$st" != stop ] && [ "$st" != after ]; then echo "== $st skipped: an earlier stage did not pass"; continue; fi
  echo "== $st $(date -u +%H:%M:%SZ)"
  n0=$(wc -l < docker/walk_session/steps.jsonl 2>/dev/null || echo 0)
  bash vm_walk_168d.sh "$st"
  if tail -n +"$((n0 + 1))" docker/walk_session/steps.jsonl | grep -q '"pass_by_exit": false'; then ok=0; echo "!! $st did not pass"; fi
done
if [ "$ok" = 1 ]; then
  echo "== render $(date -u +%H:%M:%SZ)"
  F="$HOME/q167/walk/fontpkg/root/usr/share/fonts/truetype/dejavu"
  RENDER_FONT_DIR="$F" "$HOME/q167/walk/venv/bin/python" render_cast.py docker/out/WALKTHROUGH_1.6.8.cast docker/out/WALKTHROUGH_1.6.8.mp4 > docker/walk_session/logs/render.log 2>&1
  echo "render exit $?"
  cat docker/walk_session/logs/render.log
  sha256sum docker/out/WALKTHROUGH_1.6.8.cast docker/out/WALKTHROUGH_1.6.8.mp4
fi
echo "WALK SESSION DONE ok=$ok $(date -u +%H:%M:%SZ)"
