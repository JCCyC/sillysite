#!/usr/bin/env bash
# Runs every time the dev container is (re)created -- including "Rebuild
# Container", which keeps the named `db` volume from any previous run -- not
# just the very first time. Not on every reopen of an already-existing,
# still-running container, though.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "[post-create] Installing the Claude Code CLI..."
npm install -g @anthropic-ai/claude-code --silent

echo "[post-create] Setting up Python venv..."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet

echo "[post-create] Waiting for Postgres..."
for _ in $(seq 1 30); do
    pg_isready -h db -p 5432 -U sillysite > /dev/null 2>&1 && break
    sleep 1
done

echo "[post-create] Creating tables and default admin/config rows..."
.venv/bin/python -c "import main" > /dev/null

echo "[post-create] Seeding sample F1 data (skipped if the 'db' volume was"
echo "[post-create] reused from a previous run and already has it; wipe the"
echo "[post-create] volume first for a truly fresh reseed)..."
if .venv/bin/python -c "
from database import SessionLocal
import models
db = SessionLocal()
has_data = db.query(models.Team).first() is not None
db.close()
exit(0 if has_data else 1)
"; then
    echo "[post-create] Data already present -- skipping."
else
    .venv/bin/python seed.py
fi

echo "[post-create] Building the C client..."
(cd c && make)

echo "[post-create] Building the Java client..."
(cd java && make)

cat <<'EOF'

Dev container ready.

  .venv/bin/uvicorn main:app --reload   # run the API (forwarded on :8000)
  tests/fast_check.sh                   # quick pure-API test subset
  tests/run_tests.sh                    # full suite (talks to the host's
                                         # Docker daemon -- see the socket
                                         # mount note in docker-compose.yml)
  claude                                # Claude Code (logged in already --
                                         # ~/.claude is shared from the host)
EOF
