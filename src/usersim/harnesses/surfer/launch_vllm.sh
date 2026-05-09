#!/bin/bash
# Launch vLLM for surfer harness on a GPU instance (vast.ai, etc.)
# Serves the Holo localizer model for pixel-level UI element grounding.
set -e

MODEL="${1:-Hcompany/Holo3-35B-A3B}"
MAX_MODEL_LEN="${2:-8192}"

echo "Stopping existing vLLM..."
pkill -9 -f "vllm" 2>/dev/null || true
sleep 3

echo "Starting vLLM: model=$MODEL max_model_len=$MAX_MODEL_LEN"
nohup vllm serve "$MODEL" \
    --dtype auto \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization 0.90 \
    --port 8000 \
    --trust-remote-code \
    > /tmp/vllm_surfer.log 2>&1 &

VLLM_PID=$!
echo "vLLM started (pid=$VLLM_PID)"
echo "Waiting for health check..."

for i in $(seq 1 180); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "vLLM healthy after ${i}s"
        exit 0
    fi
    sleep 1
done

echo "ERROR: vLLM did not become healthy in 180s"
echo "Check /tmp/vllm_surfer.log"
tail -20 /tmp/vllm_surfer.log
exit 1
