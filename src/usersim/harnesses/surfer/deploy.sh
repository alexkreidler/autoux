#!/bin/bash
# Deploy surfer harness v2 and run benchmarks.
#
# Architecture:
#   - Navigator + Validator: Claude Opus via Anthropic API (runs from this machine)
#   - Localizer: Holo3-35B-A3B via vLLM on vast.ai B200
#   - Browser: Kernel (cloud browser-as-a-service)
#
# The script runs LOCALLY — all API calls go out from this machine.
# The vast instance only serves the Holo localizer via SSH tunnel.
set -e

# --- Configuration ---
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
VAST_SSH_KEY="$HOME/.ssh/id_ed25519"
VAST_SSH_OPTS="-i $VAST_SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10"

# Parse args
SUITE="${1:-easy}"    # easy, hard, all, or a task name
MODE="${2:-hybrid}"   # hybrid (Claude+Holo), claude-only
VAST_PORT="${3:-14456}"
VAST_HOST="${4:-ssh6.vast.ai}"

echo "=== Surfer Harness v2 Deployment ==="
echo "Suite: $SUITE"
echo "Mode:  $MODE"
echo "Vast:  $VAST_HOST:$VAST_PORT"
echo "====================================="

# --- Load environment ---
if [ -f "$HOME/.env" ]; then
    set -a
    source <(grep -v '^\s*#' "$HOME/.env" | grep -v '^\s*$')
    set +a
fi

# Verify keys
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set"
    exit 1
fi
if [ -z "$KERNEL_API_KEY" ]; then
    echo "ERROR: KERNEL_API_KEY not set"
    exit 1
fi
echo "Anthropic key: ${ANTHROPIC_API_KEY:0:20}..."
echo "Kernel key: ${KERNEL_API_KEY:0:20}..."

# --- Step 1: Setup vLLM tunnel (hybrid mode) ---
EXTRA_ARGS=""
if [ "$MODE" = "hybrid" ]; then
    echo ""
    echo "[1/3] Setting up SSH tunnel to vast.ai for Holo localizer..."

    # Kill any existing tunnel on port 18000
    lsof -ti:18000 2>/dev/null | xargs kill 2>/dev/null || true

    # Check if vast instance is reachable
    if ssh $VAST_SSH_OPTS -p "$VAST_PORT" "root@$VAST_HOST" "echo ok" 2>/dev/null; then
        echo "Vast instance reachable."

        # Check if vLLM is running
        VLLM_STATUS=$(ssh $VAST_SSH_OPTS -p "$VAST_PORT" "root@$VAST_HOST" \
            "curl -sf http://localhost:8000/health 2>/dev/null && echo healthy || echo down")

        if [ "$VLLM_STATUS" = "healthy" ]; then
            echo "vLLM already running and healthy on vast instance."
        else
            echo "vLLM not running. Starting on vast instance..."
            scp $VAST_SSH_OPTS -P "$VAST_PORT" \
                "$LOCAL_DIR/launch_vllm.sh" \
                "root@$VAST_HOST:/root/"
            ssh $VAST_SSH_OPTS -p "$VAST_PORT" "root@$VAST_HOST" \
                "cd /root && bash launch_vllm.sh Hcompany/Holo3-35B-A3B 8192"
        fi

        # Create SSH tunnel: local 18000 -> remote 8000
        ssh $VAST_SSH_OPTS -p "$VAST_PORT" -L 18000:localhost:8000 -N -f "root@$VAST_HOST"
        echo "SSH tunnel: localhost:18000 -> vast:8000"
        export VLLM_BASE="http://localhost:18000"

        # Verify tunnel works
        sleep 2
        if curl -sf http://localhost:18000/health > /dev/null 2>&1; then
            echo "Tunnel verified: vLLM healthy via tunnel"
        else
            echo "WARNING: Tunnel not working, falling back to claude-only mode"
            MODE="claude-only"
        fi
    else
        echo "WARNING: Cannot reach vast instance, falling back to claude-only mode"
        MODE="claude-only"
    fi
fi

if [ "$MODE" = "claude-only" ]; then
    echo ""
    echo "[1/3] Claude-only mode: no vLLM/Holo needed"
    EXTRA_ARGS="--claude-only"
fi

# --- Step 2: Run benchmark ---
echo ""
echo "[2/3] Running benchmark: $SUITE (mode: $MODE)"

if [[ "$SUITE" == "easy" || "$SUITE" == "hard" || "$SUITE" == "all" ]]; then
    SUITE_ARG="--suite $SUITE"
else
    SUITE_ARG="--task $SUITE"
fi

cd "$LOCAL_DIR"
python3 -m usersim.harnesses.surfer $SUITE_ARG $EXTRA_ARGS --label "${MODE}_${SUITE}" \
    || python3 harness.py $SUITE_ARG $EXTRA_ARGS --label "${MODE}_${SUITE}"

# --- Step 3: Cleanup ---
echo ""
echo "[3/3] Cleanup..."
lsof -ti:18000 2>/dev/null | xargs kill 2>/dev/null || true

echo ""
echo "=== Done ==="
echo "Results: data/surfer_results_*.json"
echo "Traces:  data/traces/"
