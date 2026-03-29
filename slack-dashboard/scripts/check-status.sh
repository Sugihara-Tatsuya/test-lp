#!/bin/bash
# Check the status of the Slack Dashboard auto-update

echo "=== LaunchAgent Status ==="
launchctl list 2>/dev/null | grep slack-dashboard || echo "Not loaded"

echo ""
echo "=== Last 20 log lines ==="
LOG="/Users/sugiharatatsuya/Desktop/claudecode_demo/slack-dashboard/logs/update.log"
if [[ -f "${LOG}" ]]; then
    tail -20 "${LOG}"
else
    echo "No log file yet"
fi

echo ""
echo "=== Last deploy ==="
cd /Users/sugiharatatsuya/Desktop/claudecode_demo
git log --oneline -3 -- docs/slack-dashboard.html 2>/dev/null || echo "No commits found"
