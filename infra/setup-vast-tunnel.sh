#!/usr/bin/env bash
# setup-vast-tunnel.sh — Install cloudflared on a VAST.ai GPU instance and
# connect it to a Cloudflare tunnel so vLLM is reachable at a public hostname.
#
# Prerequisites:
#   - SSH access to the VAST instance (~/.ssh/id_ed25519 registered with vast.ai)
#   - Cloudflare API credentials: CF_EMAIL and CF_GLOBAL_API_KEY
#     (defaults read from ~/.env if present)
#   - A Cloudflare-managed domain (default: alexkreidler.com)
#
# Usage:
#   ./setup-vast-tunnel.sh                         # uses defaults
#   ./setup-vast-tunnel.sh --ssh-host ssh6.vast.ai --ssh-port 14456
#   HOSTNAME=llm ./setup-vast-tunnel.sh            # creates llm.alexkreidler.com
#
# What it does:
#   1. Creates a Cloudflare tunnel (named "vast-gpu")
#   2. Configures ingress: <HOSTNAME>.<DOMAIN> -> http://127.0.0.1:8000
#   3. Creates a CNAME DNS record
#   4. Installs cloudflared on the VAST instance
#   5. Starts cloudflared as a background process
#   6. Verifies connectivity
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
DOMAIN="${DOMAIN:-alexkreidler.com}"
HOSTNAME="${HOSTNAME:-gpu}"                    # subdomain — results in gpu.alexkreidler.com
FQDN="${HOSTNAME}.${DOMAIN}"
TUNNEL_NAME="${TUNNEL_NAME:-vast-gpu}"
ORIGIN_SERVICE="${ORIGIN_SERVICE:-http://127.0.0.1:8000}"

SSH_HOST="${SSH_HOST:-ssh6.vast.ai}"
SSH_PORT="${SSH_PORT:-14456}"
SSH_USER="${SSH_USER:-root}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"

# Load secrets from ~/.env if not already set
if [[ -z "${CF_GLOBAL_API_KEY:-}" || -z "${CF_EMAIL:-}" ]]; then
  if [[ -f "$HOME/.env" ]]; then
    CF_GLOBAL_API_KEY="${CF_GLOBAL_API_KEY:-$(grep '^CF_GLOBAL_API_KEY=' "$HOME/.env" | cut -d= -f2)}"
    CF_EMAIL="${CF_EMAIL:-$(grep '^CF_EMAIL=' "$HOME/.env" | cut -d= -f2)}"
  fi
fi

if [[ -z "${CF_GLOBAL_API_KEY:-}" || -z "${CF_EMAIL:-}" ]]; then
  echo "ERROR: CF_GLOBAL_API_KEY and CF_EMAIL must be set (or present in ~/.env)"
  exit 1
fi

# Parse CLI overrides
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ssh-host)  SSH_HOST="$2"; shift 2 ;;
    --ssh-port)  SSH_PORT="$2"; shift 2 ;;
    --ssh-user)  SSH_USER="$2"; shift 2 ;;
    --ssh-key)   SSH_KEY="$2"; shift 2 ;;
    --domain)    DOMAIN="$2"; FQDN="${HOSTNAME}.${DOMAIN}"; shift 2 ;;
    --hostname)  HOSTNAME="$2"; FQDN="${HOSTNAME}.${DOMAIN}"; shift 2 ;;
    --origin)    ORIGIN_SERVICE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

SSH_CMD="ssh -i ${SSH_KEY} -p ${SSH_PORT} -o ConnectTimeout=15 -o ServerAliveInterval=10 -o StrictHostKeyChecking=no ${SSH_USER}@${SSH_HOST}"

cf_api() {
  # $1 = method, $2 = path (relative to /client/v4), $3 = optional JSON body
  local method="$1" path="$2" body="${3:-}"
  local args=(-s -X "$method"
    "https://api.cloudflare.com/client/v4${path}"
    -H "X-Auth-Email: ${CF_EMAIL}"
    -H "X-Auth-Key: ${CF_GLOBAL_API_KEY}"
    -H "Content-Type: application/json")
  [[ -n "$body" ]] && args+=(--data "$body")
  curl "${args[@]}"
}

echo "==> Resolving Cloudflare account & zone..."
ACCOUNT_ID=$(cf_api GET "/accounts?per_page=1" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")
ZONE_ID=$(cf_api GET "/zones?name=${DOMAIN}" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")
echo "    Account: ${ACCOUNT_ID}"
echo "    Zone:    ${ZONE_ID} (${DOMAIN})"

# ── Step 1: Create tunnel ─────────────────────────────────────────────────────
echo "==> Checking for existing tunnel '${TUNNEL_NAME}'..."
EXISTING=$(cf_api GET "/accounts/${ACCOUNT_ID}/cfd_tunnel?name=${TUNNEL_NAME}&is_deleted=false" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")

if [[ -n "$EXISTING" ]]; then
  TUNNEL_ID="$EXISTING"
  echo "    Found existing tunnel: ${TUNNEL_ID}"
  TOKEN=$(cf_api GET "/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/token" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['result'])")
else
  echo "    Creating new tunnel..."
  TUNNEL_SECRET=$(openssl rand -base64 32)
  RESULT=$(cf_api POST "/accounts/${ACCOUNT_ID}/cfd_tunnel" \
    "{\"name\":\"${TUNNEL_NAME}\",\"tunnel_secret\":\"${TUNNEL_SECRET}\",\"config_src\":\"cloudflare\"}")
  TUNNEL_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['id'])")
  TOKEN=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['token'])")
  echo "    Created tunnel: ${TUNNEL_ID}"
fi

# ── Step 2: Configure tunnel ingress ──────────────────────────────────────────
echo "==> Configuring tunnel ingress: ${FQDN} -> ${ORIGIN_SERVICE}"
cf_api PUT "/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/configurations" \
  "{\"config\":{\"ingress\":[{\"hostname\":\"${FQDN}\",\"service\":\"${ORIGIN_SERVICE}\",\"originRequest\":{}},{\"service\":\"http_status:404\"}]}}" \
  > /dev/null
echo "    Done."

# ── Step 3: Create DNS record ─────────────────────────────────────────────────
echo "==> Creating DNS CNAME: ${FQDN} -> ${TUNNEL_ID}.cfargotunnel.com"
# Delete existing record if present
EXISTING_DNS=$(cf_api GET "/zones/${ZONE_ID}/dns_records?name=${FQDN}&type=CNAME" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")
if [[ -n "$EXISTING_DNS" ]]; then
  cf_api DELETE "/zones/${ZONE_ID}/dns_records/${EXISTING_DNS}" > /dev/null
  echo "    Deleted old record."
fi
cf_api POST "/zones/${ZONE_ID}/dns_records" \
  "{\"type\":\"CNAME\",\"name\":\"${HOSTNAME}\",\"content\":\"${TUNNEL_ID}.cfargotunnel.com\",\"proxied\":true}" \
  > /dev/null
echo "    Done."

# ── Step 4: Install cloudflared on VAST ───────────────────────────────────────
echo "==> Installing cloudflared on VAST (${SSH_HOST}:${SSH_PORT})..."
${SSH_CMD} 'which cloudflared > /dev/null 2>&1 && echo "already installed" || {
  curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
  dpkg -i /tmp/cloudflared.deb
  echo "installed $(cloudflared --version)"
}'

# ── Step 5: Start cloudflared ─────────────────────────────────────────────────
echo "==> Starting cloudflared on VAST..."
# shellcheck disable=SC2029
${SSH_CMD} "
  # Kill any existing cloudflared
  pgrep -f 'cloudflared tunnel' | xargs -r kill 2>/dev/null || true
  sleep 1
  # Start in background, detached from session
  nohup cloudflared tunnel --no-autoupdate run --token ${TOKEN} \
    > /var/log/cloudflared.log 2>&1 &
  disown
  echo 'PID:' \$!
  sleep 3
  if pgrep -f 'cloudflared tunnel' > /dev/null; then
    echo 'cloudflared is running'
  else
    echo 'ERROR: cloudflared failed to start'
    tail -10 /var/log/cloudflared.log
    exit 1
  fi
"

# ── Step 6: Verify ────────────────────────────────────────────────────────────
echo "==> Waiting for tunnel to propagate..."
sleep 5
for i in $(seq 1 12); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://${FQDN}/v1/models" 2>/dev/null || echo "000")
  if [[ "$HTTP_CODE" == "200" ]]; then
    echo "==> SUCCESS: https://${FQDN} is reachable (HTTP 200)"
    echo ""
    echo "Endpoints:"
    echo "  Base URL:         https://${FQDN}/v1"
    echo "  Models:           https://${FQDN}/v1/models"
    echo "  Chat completions: https://${FQDN}/v1/chat/completions"
    echo ""
    echo "WebArena env:"
    echo "  export VLLM_BASE_URL=https://${FQDN}/v1"
    echo "  export VLLM_API_KEY=dummy"
    exit 0
  fi
  echo "    Attempt ${i}/12: HTTP ${HTTP_CODE}, retrying..."
  sleep 5
done

echo "WARNING: Tunnel created but endpoint not yet reachable."
echo "  The vLLM server may still be starting. Check with:"
echo "  curl https://${FQDN}/v1/models"
