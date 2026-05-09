#!/usr/bin/env bash
# check-status.sh — Verify VAST instance, vLLM, cloudflared, and tunnel health.
set -euo pipefail

SSH_HOST="${SSH_HOST:-ssh6.vast.ai}"
SSH_PORT="${SSH_PORT:-14456}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
FQDN="${FQDN:-gpu.alexkreidler.com}"

SSH_CMD="ssh -i ${SSH_KEY} -p ${SSH_PORT} -o ConnectTimeout=10 -o ServerAliveInterval=10 -o StrictHostKeyChecking=no root@${SSH_HOST}"

echo "=== VAST Instance ==="
if ${SSH_CMD} 'echo "connected"' 2>/dev/null; then
  echo "  SSH: OK"
else
  echo "  SSH: FAILED (instance may be stopped)"
  exit 1
fi

echo ""
echo "=== GPU ==="
${SSH_CMD} 'nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader'

echo ""
echo "=== vLLM ==="
${SSH_CMD} '
  if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "  Status: HEALTHY"
    MODEL=$(curl -s http://127.0.0.1:8000/v1/models | python3 -c "import sys,json; print(json.load(sys.stdin)[\"data\"][0][\"id\"])" 2>/dev/null)
    echo "  Model: ${MODEL}"
  else
    echo "  Status: DOWN"
    echo "  Run: ./launch-vllm.sh"
  fi
'

echo ""
echo "=== cloudflared ==="
${SSH_CMD} '
  if pgrep -f "cloudflared tunnel" > /dev/null 2>&1; then
    echo "  Status: RUNNING"
  else
    echo "  Status: DOWN"
    echo "  Run: ./setup-vast-tunnel.sh"
  fi
'

echo ""
echo "=== Tunnel Endpoint ==="
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://${FQDN}/v1/models" 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
  echo "  https://${FQDN}: OK (HTTP 200)"
else
  echo "  https://${FQDN}: UNREACHABLE (HTTP ${HTTP_CODE})"
fi
