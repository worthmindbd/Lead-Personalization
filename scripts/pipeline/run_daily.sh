#!/usr/bin/env bash
set -eo pipefail

# Project root resolution
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Ensure rclone and node/npm are in PATH for non-login cron shells
export PATH="/home/worthmind/.local/bin:/home/worthmind/.nvm/versions/node/v24.19.0/bin:$PATH"

# Log directory setup
LOG_DIR="$PROJECT_ROOT/.pipeline/logs"
mkdir -p "$LOG_DIR"
TODAY="$(date +'%Y-%m-%d')"
LOG_FILE="$LOG_DIR/daily_$TODAY.log"

echo "================================================================================" >> "$LOG_FILE"
echo "Daily pipeline run started at $(date -Iseconds)" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"

# Execute the orchestrator
"$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/scripts/pipeline/run_pipeline.py" "$@" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"
echo "Daily pipeline run finished at $(date -Iseconds) with exit code $EXIT_CODE" >> "$LOG_FILE"
echo "================================================================================" >> "$LOG_FILE"

exit $EXIT_CODE
