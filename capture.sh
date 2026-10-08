#!/usr/bin/env bash
# Capture desktop + mobile screenshots of CAPTURE_URL into CAPTURE_DIR.
set -euo pipefail
/usr/bin/time -p test -n "${CAPTURE_URL:-}" || { echo "CAPTURE_URL is required" >&2; exit 1; }
/usr/bin/time -p test -n "${CAPTURE_DIR:-}" || { echo "CAPTURE_DIR is required" >&2; exit 1; }
/usr/bin/time -p mkdir -p "$CAPTURE_DIR"
command -v playwright-cli >/dev/null || { echo "playwright-cli not found" >&2; exit 1; }

SESSION="capture-$$"
fail_temp() { echo "TRANSIENT: $*" >&2; /usr/bin/time -p playwright-cli -s="$SESSION" close 2>/dev/null || true; exit 75; }
fail_perm() { echo "PERMANENT: $*" >&2; /usr/bin/time -p playwright-cli -s="$SESSION" close 2>/dev/null || true; exit 1; }

/usr/bin/time -p playwright-cli -s="$SESSION" open "$CAPTURE_URL" || fail_temp "browser open failed"

shot() { # $1=name $2=width $3=height
  /usr/bin/time -p playwright-cli -s="$SESSION" goto "$CAPTURE_URL" || fail_temp "navigation failed ($1)"
  /usr/bin/time -p playwright-cli -s="$SESSION" resize "$2" "$3" || fail_temp "resize failed ($1)"
  # Wait for rendered content: body visible + non-empty text (app is static Arabic UI).
  /usr/bin/time -p playwright-cli -s="$SESSION" eval "(async () => { const t0 = Date.now(); while (Date.now() - t0 < 15000) { const b = document.querySelector('body'); if (b && b.innerText.trim().length > 20 && document.fonts.status === 'loaded') return 'ready:' + b.innerText.slice(0, 40); await new Promise(r => setTimeout(r, 300)); } return 'timeout'; })()" || fail_temp "readiness probe failed ($1)"
  /usr/bin/time -p playwright-cli -s="$SESSION" screenshot --filename="$CAPTURE_DIR/final-$1.png" || fail_temp "screenshot failed ($1)"
  /usr/bin/time -p test -s "$CAPTURE_DIR/final-$1.png" || fail_perm "screenshot empty/missing ($1)"
}

time -p shot desktop 1440 900
time -p shot mobile 390 844

/usr/bin/time -p playwright-cli -s="$SESSION" close || fail_temp "browser close failed"
echo "Captures saved to $CAPTURE_DIR"
