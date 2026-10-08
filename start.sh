#!/usr/bin/env bash
# PY Guard — startup: build static dist/ and serve it in the foreground on PORT (default 3000).
set -euo pipefail
cd "$(dirname "$0")"
/usr/bin/time -p python3 --version
/usr/bin/time -p python3 build_dist.py
/usr/bin/time -p test -f dist/index.html
# Publish deployment output for the controller (built static dir must stay inside PROJECT_DIR).
/usr/bin/time -p python3 - "$PWD/dist" <<'EOF'
import json, os, sys
project = os.getcwd()
directory = sys.argv[1]
web_dir = os.environ.get("OPENCODE_WEB_DIR", "/home/runner/work/_temp/omgithub-web")
os.makedirs(web_dir, exist_ok=True)
payload = {"project": project, "directory": directory}
with open(os.path.join(web_dir, "deployment-output.json"), "w", encoding="utf-8") as f:
    json.dump(payload, f)
print("deployment-output:", payload)
EOF
PORT="${PORT:-3000}"
echo "Serving $PWD/dist on port $PORT"
exec python3 -m http.server "$PORT" --directory dist
