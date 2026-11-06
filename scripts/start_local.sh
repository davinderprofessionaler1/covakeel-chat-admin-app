#!/usr/bin/env bash
# Start this checkout's services. Ctrl+C stops processes started by this script.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$PROJECT_DIR/backend/.venv/bin/python"
FRONTEND_PORT="${FRONTEND_PORT:-8081}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
PIDS=()
cleanup() {
  if ((${#PIDS[@]})); then
    kill "${PIDS[@]}" 2>/dev/null || true
    wait "${PIDS[@]}" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 0' INT TERM
mkdir -p "$PROJECT_DIR/.local/logs" "$PROJECT_DIR/.local/mongodb-data"
"$PYTHON" - "$FRONTEND_PORT" <<'CHECK'
import socket, sys
for port in (8000, int(sys.argv[1])):
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            raise SystemExit(f"Port {port} is already in use. Stop the earlier app first.")
CHECK
if ! "$PYTHON" - <<'CHECK'
import socket
try:
    with socket.create_connection(("127.0.0.1",27017),timeout=1): pass
except OSError:
    raise SystemExit(1)
CHECK
then
  "$PROJECT_DIR/.local/mongodb/mongod" \
    --dbpath "$PROJECT_DIR/.local/mongodb-data" \
    --logpath "$PROJECT_DIR/.local/logs/mongodb.log" \
    --bind_ip 127.0.0.1 --port 27017 --wiredTigerCacheSizeGB 0.5 &
  PIDS+=("$!")
fi
"$PYTHON" - <<'CHECK'
import time
from pymongo import MongoClient
client=MongoClient("mongodb://127.0.0.1:27017",serverSelectionTimeoutMS=1000)
for attempt in range(30):
    try:
        client.admin.command("ping")
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("MongoDB did not start; inspect .local/logs/mongodb.log")
client.close()
CHECK
(cd "$PROJECT_DIR/backend" && exec "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
PIDS+=("$!")
"$PYTHON" - <<'CHECK'
import time, urllib.request
for attempt in range(30):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/",timeout=2) as r:
            assert r.status==200
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Backend did not become healthy")
CHECK
(cd "$PROJECT_DIR/frontend" && exec node node_modules/vite/bin/vite.js --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --strictPort) &
PIDS+=("$!")
printf 'Frontend: http://127.0.0.1:%s\nAPI docs: http://127.0.0.1:8000/docs\nCtrl+C stops this session.\n' "$FRONTEND_PORT"
wait -n "${PIDS[@]}"
