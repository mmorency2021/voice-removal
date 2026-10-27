#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg is required. On macOS: brew install ffmpeg. On Ubuntu: sudo apt install ffmpeg."
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  task_python=""
  for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then task_python="$candidate"; break; fi
  done
  if [[ -z "$task_python" ]]; then echo "Install Python 3.11 or 3.12 first."; exit 1; fi
  "$task_python" -m venv .venv
fi
if [[ ! -f .venv/.audio-tools-ready ]]; then
  .venv/bin/python -m pip install -r requirements.txt
  touch .venv/.audio-tools-ready
fi
exec .venv/bin/python -u app.py "$@"
