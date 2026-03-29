#!/bin/bash
# Slack Dashboard auto-update script
# Runs: collector → generate_static → git commit & push
set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────
PROJECT_ROOT="/Users/sugiharatatsuya/Desktop/claudecode_demo"
DASHBOARD_DIR="${PROJECT_ROOT}/slack-dashboard"
LOG_DIR="${DASHBOARD_DIR}/logs"
LOG_FILE="${LOG_DIR}/update.log"
LOCK_DIR="/tmp/slack-dashboard-update.lock"
PYTHON="/usr/bin/python3"
export PATH="/usr/bin:/usr/local/bin:/usr/sbin:/sbin"

# ── Logging ────────────────────────────────────────────────────
mkdir -p "${LOG_DIR}"

# Rotate log if > 1MB
if [[ -f "${LOG_FILE}" ]] && [[ $(stat -f%z "${LOG_FILE}" 2>/dev/null || echo 0) -gt 1048576 ]]; then
    mv "${LOG_FILE}" "${LOG_FILE}.1"
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# ── Lock (prevent overlapping runs) ───────────────────────────
if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
    # Check if stale lock (older than 6 hours)
    lock_age=$(( $(date +%s) - $(stat -f%m "${LOCK_DIR}" 2>/dev/null || echo 0) ))
    if [[ ${lock_age} -gt 21600 ]]; then
        log "WARN: Removing stale lock (${lock_age}s old)"
        rm -rf "${LOCK_DIR}"
        mkdir "${LOCK_DIR}"
    else
        log "SKIP: Another update is running (lock age: ${lock_age}s)"
        exit 0
    fi
fi
trap 'rm -rf "${LOCK_DIR}"' EXIT

log "===== Update started ====="

# ── Load environment ──────────────────────────────────────────
if [[ -f "${DASHBOARD_DIR}/.env" ]]; then
    set -a
    source "${DASHBOARD_DIR}/.env"
    set +a
else
    log "ERROR: .env not found"
    exit 1
fi

# ── Step 1: Collect data ──────────────────────────────────────
log "Step 1: Running collector..."
cd "${DASHBOARD_DIR}"
if ${PYTHON} collector.py >> "${LOG_FILE}" 2>&1; then
    log "Step 1: Collector completed successfully"
else
    log "WARN: Collector failed (exit $?), continuing with existing data"
fi

# ── Step 2: Generate static HTML ──────────────────────────────
log "Step 2: Generating dashboard..."
if ${PYTHON} generate_static.py >> "${LOG_FILE}" 2>&1; then
    log "Step 2: Dashboard generated successfully"
else
    log "ERROR: Dashboard generation failed"
    osascript -e 'display notification "Dashboard生成に失敗しました" with title "Slack Dashboard"' 2>/dev/null || true
    exit 0
fi

# ── Step 3: Git commit & push ─────────────────────────────────
log "Step 3: Deploying to GitHub Pages..."
cd "${PROJECT_ROOT}"

git add docs/slack-dashboard.html slack-dashboard/docs/index.html 2>> "${LOG_FILE}"

if git diff --cached --quiet; then
    log "Step 3: No changes to deploy"
else
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
    if git commit -m "Auto-update Slack dashboard ${TIMESTAMP}" >> "${LOG_FILE}" 2>&1; then
        if git push origin main >> "${LOG_FILE}" 2>&1; then
            log "Step 3: Pushed to GitHub Pages"
        else
            log "WARN: Git push failed, will retry next run"
            osascript -e 'display notification "GitHub Pagesへのpushに失敗しました" with title "Slack Dashboard"' 2>/dev/null || true
        fi
    else
        log "WARN: Git commit failed"
    fi
fi

log "===== Update completed ====="
