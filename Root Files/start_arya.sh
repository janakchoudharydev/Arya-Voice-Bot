#!/bin/bash
# ================================================
# ARYA Startup Script with Sleep Prevention
# ================================================
# This script uses 'caffeinate' to prevent Mac from
# sleeping while ARYA is running.
#
# Usage:
#   ./start_arya.sh        - Normal start (prevents idle sleep)
#   ./start_arya.sh --full - Full prevention (no display/disk/system sleep)
#
# To stop: Press Ctrl+C
# ================================================

cd "$(dirname "$0")"

echo "🚀 Starting ARYA with sleep prevention..."
echo "   Press Ctrl+C to stop"
echo ""

# Ensure we use the virtual environment Python (which is in the parent directory)
PYTHON_EXEC="../venv/bin/python3"
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python3" # Fallback to system if venv not found
fi

if [ "$1" == "--full" ]; then
    echo "⚡ Full sleep prevention mode (display + disk + system)"
    caffeinate -dims $PYTHON_EXEC ../core/agent.py dev
else
    echo "💤 Idle sleep prevention mode"
    caffeinate -i $PYTHON_EXEC ../core/agent.py dev
fi
