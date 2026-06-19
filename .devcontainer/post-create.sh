#!/usr/bin/env bash
# Runs once when the dev container is first created (not on every reopen).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

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

echo "[post-create] Seeding sample F1 data (one-off; re-running this script"
echo "[post-create] later would duplicate it -- wipe the 'db' volume first if"
echo "[post-create] you want a truly fresh reseed)..."
.venv/bin/python seed.py

echo "[post-create] Building the C client..."
(cd c && make)

cat <<'EOF'

Dev container ready.

  .venv/bin/uvicorn main:app --reload   # run the API (forwarded on :8000)
  tests/fast_check.sh                   # quick pure-API test subset
  tests/run_tests.sh                    # full suite (needs Docker -- see
                                         # the docker-outside-of-docker note
                                         # in .devcontainer/docker-compose.yml)
EOF
