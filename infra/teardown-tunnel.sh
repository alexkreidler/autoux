#!/usr/bin/env bash
# teardown-tunnel.sh — Remove the Cloudflare tunnel and DNS record.
# Use this when you're done with the VAST instance to clean up.
set -euo pipefail

DOMAIN="${DOMAIN:-alexkreidler.com}"
HOSTNAME="${HOSTNAME:-gpu}"
FQDN="${HOSTNAME}.${DOMAIN}"
TUNNEL_NAME="${TUNNEL_NAME:-vast-gpu}"

if [[ -f "$HOME/.env" ]]; then
  CF_GLOBAL_API_KEY="${CF_GLOBAL_API_KEY:-$(grep '^CF_GLOBAL_API_KEY=' "$HOME/.env" | cut -d= -f2)}"
  CF_EMAIL="${CF_EMAIL:-$(grep '^CF_EMAIL=' "$HOME/.env" | cut -d= -f2)}"
fi

cf_api() {
  local method="$1" path="$2" body="${3:-}"
  local args=(-s -X "$method"
    "https://api.cloudflare.com/client/v4${path}"
    -H "X-Auth-Email: ${CF_EMAIL}"
    -H "X-Auth-Key: ${CF_GLOBAL_API_KEY}"
    -H "Content-Type: application/json")
  [[ -n "$body" ]] && args+=(--data "$body")
  curl "${args[@]}"
}

ACCOUNT_ID=$(cf_api GET "/accounts?per_page=1" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")
ZONE_ID=$(cf_api GET "/zones?name=${DOMAIN}" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")

echo "==> Deleting DNS record: ${FQDN}"
DNS_ID=$(cf_api GET "/zones/${ZONE_ID}/dns_records?name=${FQDN}&type=CNAME" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")
if [[ -n "$DNS_ID" ]]; then
  cf_api DELETE "/zones/${ZONE_ID}/dns_records/${DNS_ID}" > /dev/null
  echo "    Deleted."
else
  echo "    Not found, skipping."
fi

echo "==> Deleting tunnel: ${TUNNEL_NAME}"
TUNNEL_ID=$(cf_api GET "/accounts/${ACCOUNT_ID}/cfd_tunnel?name=${TUNNEL_NAME}&is_deleted=false" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")
if [[ -n "$TUNNEL_ID" ]]; then
  # Must clean up connections first
  cf_api DELETE "/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}/connections" > /dev/null 2>&1 || true
  cf_api DELETE "/accounts/${ACCOUNT_ID}/cfd_tunnel/${TUNNEL_ID}" > /dev/null
  echo "    Deleted tunnel ${TUNNEL_ID}."
else
  echo "    Not found, skipping."
fi

echo "==> Done. Tunnel and DNS cleaned up."
