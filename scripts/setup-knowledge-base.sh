#!/usr/bin/env bash
# One implementation on Windows, Linux, and macOS; requires PowerShell 7.
# Usage: ./scripts/setup-knowledge-base.sh [-EnvironmentName <azd-environment>] [-CheckOnly]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v pwsh >/dev/null 2>&1; then
  echo "PowerShell 7 (pwsh) is required. Run scripts/setup-knowledge-base.ps1 after installing it." >&2
  exit 1
fi
exec pwsh -NoLogo -NoProfile -File "$SCRIPT_DIR/setup-knowledge-base.ps1" "$@"
