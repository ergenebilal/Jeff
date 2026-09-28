#!/bin/bash
# Clean up old QC reports — keep newest 5 per product
QC_DIR="/home/hermes/dijital-urunler/qc-reports"
for prefix in agent-reach-pack ai-agency-starter n8n-playbook prompt-pack zero-to-ai-agent; do
    files=$(ls -1t "$QC_DIR"/"${prefix}"_qc_*.md 2>/dev/null | tail -n +6)
    if [ -n "$files" ]; then
        echo "$files" | xargs rm -f
        echo "Cleaned $prefix: removed $(echo "$files" | wc -l) old reports"
    else
        echo "No extra reports for $prefix"
    fi
done
