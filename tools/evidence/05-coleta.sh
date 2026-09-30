#!/usr/bin/env bash
set -euo pipefail

DIR="${1:?uso: 05-coleta.sh <pasta-de-evidencia>}"
DIR="${DIR%/}"
ARCHIVE="$DIR.tar.gz"

tar -czf "$ARCHIVE" -C "$(dirname "$DIR")" "$(basename "$DIR")"
ls -lh "$ARCHIVE"
