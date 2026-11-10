#!/usr/bin/env bash
set -eu
here="$(cd "$(dirname "$0")/../../courses/zeo-itam-autumn-2026/labs/10-telegram-from-zero-2026-11-03/mantle-alternative" && pwd)"
UV_PROJECT_ENVIRONMENT="$HOME/.venv-mantle" uv sync --locked --python 3.12 --project "$here"
echo "Lucy's shop is ready. In the terminal run: bash run.sh"
