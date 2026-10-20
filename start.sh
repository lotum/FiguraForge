#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  # macOS may put Apple's Python 3.9 before a supported Homebrew Python.
  forge_python=""
  for candidate in python3.13 python3.12 python3.14 python3.11 python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
      forge_python="$candidate"
      break
    fi
  done
  if [ -z "$forge_python" ]; then
    echo 'FiguraForge braucht Python >= 3.11 (empfohlen: 3.13). Bitte installieren und erneut starten.' >&2
    exit 1
  fi
  "$forge_python" -m venv .venv
fi
if [ ! -f .venv/.figuraforge-installed ]; then
  # Environments created by uv may intentionally have no pip yet.
  if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    .venv/bin/python -m ensurepip --upgrade
  fi
  .venv/bin/python -m pip install -c requirements-tested.txt -e .
  touch .venv/.figuraforge-installed
fi
exec .venv/bin/python scripts/run.py "$@"
