#!/usr/bin/env bash
# Build the distributable archive uploaded to Itch.io.
#
# Usage: ./build.sh
#
# The script freezes the game with PyInstaller, drops the configuration
# file next to the produced binary so players can edit it, and zips the
# whole thing under a platform-tagged name.  It is deliberately plain so
# that it can be re-run from scratch during the peer review.

set -euo pipefail

PYTHON="${PYTHON:-python3}"
NAME="pac-man"
WHEEL="mazegenerator-2.1.0-py3-none-any.whl"
STAGE="dist/release"

cd "$(dirname "$0")"

case "$(uname -s)" in
    Linux*)   PLATFORM="linux" ;;
    Darwin*)  PLATFORM="macos" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
    *)        PLATFORM="unknown" ;;
esac

echo ">>> checking the toolchain"
"$PYTHON" -c "import PyInstaller" 2>/dev/null || {
    echo "PyInstaller is missing; run 'make install' first." >&2
    exit 1
}
"$PYTHON" -c "import pygame" 2>/dev/null || {
    echo "pygame is missing; run 'make install' first." >&2
    exit 1
}
"$PYTHON" -c "import mazegenerator" 2>/dev/null || {
    echo "The A-Maze-ing package is missing; install ${WHEEL}." >&2
    exit 1
}

echo ">>> cleaning previous builds"
rm -rf build dist

echo ">>> freezing the game"
"$PYTHON" -m PyInstaller --noconfirm --clean pacman.spec

echo ">>> staging the release"
mkdir -p "$STAGE"
if [ -f "dist/${NAME}.exe" ]; then
    mv "dist/${NAME}.exe" "$STAGE/"
else
    mv "dist/${NAME}" "$STAGE/"
    chmod +x "${STAGE}/${NAME}"
fi
cp config.json README.md "$STAGE/"

ARCHIVE="${NAME}-${PLATFORM}.zip"
echo ">>> packing dist/${ARCHIVE}"
(cd dist && "$PYTHON" -m zipfile -c "$ARCHIVE" release)

echo ">>> done: dist/${ARCHIVE}"
