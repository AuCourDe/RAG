#!/bin/bash
# Skrypt do monitorowania logow diagnostycznych w czasie rzeczywistym

LOG_DIR="/home/rev/projects/RAG-Reborn/source_reference"
RAG_LOG="$LOG_DIR/rag_system.log"
WATCHDOG_LOG="$LOG_DIR/logs/file_watcher.log"

echo "Monitorowanie logow diagnostycznych..."
echo "Szukam: DIAGNOSTYKA, DEBUG, PRZYCISK"
echo "======================================"
echo ""

tail -f "$RAG_LOG" "$WATCHDOG_LOG" 2>/dev/null | grep --line-buffered -E "DIAGNOSTYKA|DEBUG|PRZYCISK|KLIKNIETY|uploaded_files|files_to_process|session_state"

