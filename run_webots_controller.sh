#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export WEBOTS_HOME="/opt/homebrew/Caskroom/webots/R2025a/Webots.app"
export PYTHONPATH="$WEBOTS_HOME/Contents/lib/controller/python"
export WEBOTS_PYTHON_EXECUTABLE="$SCRIPT_DIR/.venv-webots/bin/python"

exec "$WEBOTS_PYTHON_EXECUTABLE" "$SCRIPT_DIR/symple_controller_act_2_1.py"
