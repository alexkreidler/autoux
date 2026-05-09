#!/usr/bin/env bash
# launch-vllm.sh — Start vLLM on a VAST.ai GPU instance via SSH.
#
# Handles the quirks we discovered:
#   - Kills orphaned GPU processes that hold VRAM after crashes
#   - Uses --host 0.0.0.0 (cloudflared connects via 127.0.0.1, vLLM must listen)
#   - Sets --max-num-seqs 512 (Holo3 MoE has Mamba layers, default 1024 exceeds
#     available cache blocks on B200 at 0.90 utilization)
#   - Waits for health check before returning
#
# Usage:
#   ./launch-vllm.sh                              # defaults
#   ./launch-vllm.sh --model Hcompany/Holo3-35B-A3B --max-model-len 4096
#   ./launch-vllm.sh --ssh-host ssh6.vast.ai --ssh-port 14456
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL="${MODEL:-Hcompany/Holo3-35B-A3B}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.90}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-512}"
PORT="${PORT:-8000}"

SSH_HOST="${SSH_HOST:-ssh6.vast.ai}"
SSH_PORT="${SSH_PORT:-14456}"
SSH_USER="${SSH_USER:-root}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)          MODEL="$2"; shift 2 ;;
    --max-model-len)  MAX_MODEL_LEN="$2"; shift 2 ;;
    --gpu-mem-util)   GPU_MEM_UTIL="$2"; shift 2 ;;
    --max-num-seqs)   MAX_NUM_SEQS="$2"; shift 2 ;;
    --port)           PORT="$2"; shift 2 ;;
    --ssh-host)       SSH_HOST="$2"; shift 2 ;;
    --ssh-port)       SSH_PORT="$2"; shift 2 ;;
    --ssh-user)       SSH_USER="$2"; shift 2 ;;
    --ssh-key)        SSH_KEY="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

SSH_CMD="ssh -i ${SSH_KEY} -p ${SSH_PORT} -o ConnectTimeout=15 -o ServerAliveInterval=10 -o StrictHostKeyChecking=no ${SSH_USER}@${SSH_HOST}"

echo "==> Cleaning up existing vLLM processes..."
# shellcheck disable=SC2029
${SSH_CMD} "
  # Kill any running vLLM
  pgrep -f 'vllm' | xargs -r kill 2>/dev/null || true
  sleep 2
  # Force-kill orphaned GPU processes that hold VRAM
  nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | xargs -r kill -9 2>/dev/null || true
  sleep 2
  FREE=\$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)
  echo \"GPU memory free: \${FREE} MiB\"
"

echo "==> Starting vLLM: model=${MODEL}, max_len=${MAX_MODEL_LEN}, seqs=${MAX_NUM_SEQS}"
# shellcheck disable=SC2029
${SSH_CMD} "
  python3 -m vllm.entrypoints.openai.api_server \
    --model ${MODEL} \
    --dtype auto \
    --max-model-len ${MAX_MODEL_LEN} \
    --gpu-memory-utilization ${GPU_MEM_UTIL} \
    --max-num-seqs ${MAX_NUM_SEQS} \
    --port ${PORT} \
    --host 0.0.0.0 \
    --trust-remote-code \
    > /tmp/vllm.log 2>&1 &
  PID=\$!
  disown
  echo \"PID=\${PID}\"

  echo 'Waiting for vLLM to become healthy (model loading takes ~2-3 min)...'
  for i in \$(seq 1 180); do
    if ! kill -0 \$PID 2>/dev/null; then
      echo \"ERROR: vLLM died after \${i}s\"
      tail -10 /tmp/vllm.log
      exit 1
    fi
    if curl -sf http://127.0.0.1:${PORT}/health > /dev/null 2>&1; then
      echo \"vLLM healthy after \${i}s\"
      echo \"Model: ${MODEL}\"
      echo \"Endpoint: http://127.0.0.1:${PORT}/v1\"
      exit 0
    fi
    sleep 2
  done
  echo 'WARNING: vLLM still loading after 360s. Check /tmp/vllm.log on the instance.'
  tail -5 /tmp/vllm.log
"
