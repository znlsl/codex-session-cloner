#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
APP_NAME="aik"
VENV_DIR="${VENV_DIR:-$PROJECT_ROOT/.venv}"
EDITABLE=0
FORCE=0
PYTHON_BIN="${PYTHON_BIN:-}"

usage() {
  cat <<'EOF'
Usage: ./install.sh [--editable] [--force] [--python <python-bin>]

Options:
  --editable         Install in editable mode for local development
  --force            Recreate the local .venv before installing
  --python <bin>     Use a specific Python executable
  --help             Show this help text
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --editable)
      EDITABLE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --python)
      if [ "$#" -lt 2 ]; then
        echo "Error: --python requires a value." >&2
        exit 2
      fi
      PYTHON_BIN="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

resolve_python() {
  if [ -n "$PYTHON_BIN" ]; then
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Error: python3/python not found in PATH." >&2
    exit 127
  fi
}

resolve_python

if [ "$FORCE" -eq 1 ] && [ -d "$VENV_DIR" ]; then
  rm -rf "$VENV_DIR"
fi

echo "============================================="
echo " AI CLI Kit - Installer (Unix)"
echo "============================================="
echo "Project:   $PROJECT_ROOT"
echo "Python:    $PYTHON_BIN"
echo "Venv:      $VENV_DIR"
if [ "$EDITABLE" -eq 1 ]; then
  echo "Mode:      editable"
else
  echo "Mode:      standard"
fi

# Drop --system-site-packages: it lets Apple's bundled setuptools<61 leak in,
# which silently builds an empty UNKNOWN-0.0.0 wheel because it can't read
# the PEP 621 [project] table. Our package has zero runtime deps so an
# isolated venv is strictly safer.
"$PYTHON_BIN" -m venv "$VENV_DIR"
VENV_PYTHON="$VENV_DIR/bin/python"

# Force-upgrade pip / setuptools / wheel inside the venv before installing
# the package. This is what produces a real ``ai-cli-kit-0.2.0`` wheel with
# proper console scripts (aik / cst / cc-clean) on stock macOS Python 3.9
# where the system pip is 21.3 and setuptools is 49 — old enough that pip
# falls back to building UNKNOWN-0.0.0 from our pyproject.toml.
echo "Upgrading pip / setuptools / wheel in the local venv..."
"$VENV_PYTHON" -m pip install --quiet --upgrade pip setuptools wheel

if [ "$EDITABLE" -eq 1 ]; then
  "$VENV_PYTHON" -m pip install --no-deps -e "$PROJECT_ROOT"
else
  "$VENV_PYTHON" -m pip install --no-deps "$PROJECT_ROOT"
fi

# chmod the launcher scripts that exist. ``release.sh`` only ships in the
# git source tree (it's excluded from the user-facing release tarball) so
# we skip it when missing rather than failing the install.
for launcher in aik cc-clean codex-session-toolkit codex-session-toolkit.command install.sh install.command release.sh; do
  if [ -f "$PROJECT_ROOT/$launcher" ]; then
    chmod +x "$PROJECT_ROOT/$launcher"
  fi
done

echo ""
echo "============================================="
echo " Install complete."
echo "============================================="
echo "推荐：在项目目录里直接运行 launcher（已自动可执行）"
echo "  ./aik                # 顶层菜单（推荐入口，进 Codex / Claude 选一个）"
echo "  ./codex-session-toolkit"
echo "  ./cc-clean"
echo ""
echo "如需在任意目录用裸命令 'aik' 启动，把 venv bin 加入 PATH："
echo "  export PATH=\"$VENV_DIR/bin:\$PATH\""
echo "或者 source venv："
echo "  source \"$VENV_DIR/bin/activate\""
echo ""
echo "查看版本："
echo "  ./aik --version"
