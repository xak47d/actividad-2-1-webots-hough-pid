#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -z "${WEBOTS_HOME:-}" ]]; then
  if [[ -d "/Applications/Webots.app" ]]; then
    export WEBOTS_HOME="/Applications/Webots.app"
  else
    CASK_WEBOTS="$(ls -d /opt/homebrew/Caskroom/webots/*/Webots.app 2>/dev/null | tail -n 1 || true)"
    if [[ -n "$CASK_WEBOTS" ]]; then
      export WEBOTS_HOME="$CASK_WEBOTS"
    fi
  fi
fi

if [[ -z "${WEBOTS_HOME:-}" || ! -d "$WEBOTS_HOME" ]]; then
  echo "No se pudo detectar WEBOTS_HOME. Define la variable WEBOTS_HOME antes de ejecutar este script."
  exit 1
fi

export PYTHONPATH="$WEBOTS_HOME/Contents/lib/controller/python"

if [[ -z "${WEBOTS_PYTHON_EXECUTABLE:-}" ]]; then
  if [[ -x "$SCRIPT_DIR/.venv-webots/bin/python" ]]; then
    export WEBOTS_PYTHON_EXECUTABLE="$SCRIPT_DIR/.venv-webots/bin/python"
  else
    export WEBOTS_PYTHON_EXECUTABLE="$(command -v python3)"
  fi
fi

exec "$WEBOTS_PYTHON_EXECUTABLE" "$SCRIPT_DIR/symple_controller_act_2_1.py"
