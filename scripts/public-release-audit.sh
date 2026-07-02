#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v rg >/dev/null 2>&1; then
  echo "[public-audit] ripgrep (rg) is required" >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[public-audit] python3 is required" >&2
  exit 2
fi

found=0

echo "[public-audit] checking tracked filenames for secret-bearing files..."
tracked_secret_files="$(
  git ls-files | rg '(^|/)(\.env$|credentials\.json$|secrets\.json$|privy\.json$|solana\.json$|.*keypair.*\.json$|.*\.pem$|.*\.key$|id\.json$)' || true
)"
if [ -n "$tracked_secret_files" ]; then
  echo "[public-audit] tracked secret-like files found:" >&2
  echo "$tracked_secret_files" >&2
  found=1
fi

echo "[public-audit] scanning tracked file contents for live credentials..."
content_matches="$(
  python3 - <<'PY'
import re
import subprocess
from pathlib import Path

patterns = [
    re.compile(r"-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----"),
    re.compile(r"nvapi-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"bot[0-9]{8,}:[A-Za-z0-9_-]{30,}"),
]

for filename in subprocess.check_output(["git", "ls-files"], text=True).splitlines():
    path = Path(filename)
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "guard-secrets:allow" in line:
            continue
        if any(pattern.search(line) for pattern in patterns):
            print(f"{filename}:{lineno}:{line}")
PY
)"
if [ -n "$content_matches" ]; then
  echo "[public-audit] live secret-like content found:" >&2
  echo "$content_matches" >&2
  found=1
fi

echo "[public-audit] validating npm bin metadata..."
if ! python3 - <<'EOF'
import json
import sys
from pathlib import Path

pkg = json.loads(Path("package.json").read_text())
bin_field = pkg.get("bin", {})
if isinstance(bin_field, str):
    entries = [("default", bin_field)]
else:
    entries = list(bin_field.items())

invalid = [(name, target) for name, target in entries if str(target).startswith("./")]
if invalid:
    for name, target in invalid:
        print(f"{name}: {target}", file=sys.stderr)
    sys.exit(1)
EOF
then
  echo "[public-audit] package.json has invalid bin entries for npm publish" >&2
  found=1
fi

if [ "$found" -ne 0 ]; then
  echo "[public-audit] failed" >&2
  exit 1
fi

echo "[public-audit] passed"
