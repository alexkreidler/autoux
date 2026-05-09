# Infrastructure — Cloudflare Tunnel + VAST.ai GPU

Connects a VAST.ai GPU instance to the internet via a Cloudflare Tunnel,
making the vLLM OpenAI-compatible API available at a public HTTPS endpoint
(e.g. `https://gpu.alexkreidler.com/v1`).

## Architecture

```
Your Mac / WebArena
       |
       | HTTPS (gpu.alexkreidler.com)
       v
  Cloudflare Edge
       |
       | QUIC tunnel
       v
  cloudflared (on VAST instance)
       |
       | http://127.0.0.1:8000
       v
  vLLM (OpenAI-compatible API)
       |
       v
  NVIDIA B200 GPU
```

## Prerequisites

- **VAST.ai instance** with SSH access (`~/.ssh/id_ed25519` registered)
- **Cloudflare account** with a managed domain
- Credentials in `~/.env`:
  ```
  CF_GLOBAL_API_KEY=<your-key>
  CF_EMAIL=<your-email>
  ```

## Quick Start

```bash
# 1. Start vLLM on the VAST instance
./launch-vllm.sh

# 2. Create tunnel + DNS + install cloudflared on VAST
./setup-vast-tunnel.sh

# 3. (Optional) Install cloudflared on your Mac
./setup-local-cloudflared.sh

# 4. Use the endpoint
curl https://gpu.alexkreidler.com/v1/models
curl https://gpu.alexkreidler.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Hcompany/Holo3-35B-A3B","messages":[{"role":"user","content":"Hello"}]}'
```

## Scripts

| Script | Purpose |
|---|---|
| `launch-vllm.sh` | Start vLLM on VAST (handles GPU cleanup, health check) |
| `setup-vast-tunnel.sh` | Create Cloudflare tunnel, DNS, install+start cloudflared on VAST |
| `setup-local-cloudflared.sh` | Install cloudflared on macOS (optional, for SSH-through-tunnel) |
| `check-status.sh` | Verify all components are healthy |
| `teardown-tunnel.sh` | Delete tunnel + DNS when done |

## WebArena Integration

```bash
export VLLM_BASE_URL=https://gpu.alexkreidler.com/v1
export VLLM_API_KEY=dummy
```

## Current Instance Details

- **VAST contract**: 36414456
- **SSH**: `ssh -i ~/.ssh/id_ed25519 -p 14456 root@ssh6.vast.ai`
- **GPU**: NVIDIA B200, 183 GB VRAM
- **Model**: `Hcompany/Holo3-35B-A3B` (Qwen3 MoE 35B, max 4096 tokens)
- **Tunnel**: `vast-gpu` (ID `b7636e50-893a-4977-ac48-ed4c5e49641c`)
- **Endpoint**: `https://gpu.alexkreidler.com`

## Troubleshooting

**vLLM crashes silently**
- Usually OOM or orphaned GPU processes. `launch-vllm.sh` handles cleanup.
- Check logs: `ssh ... 'tail -50 /tmp/vllm.log'`
- Common error: `max_num_seqs exceeds Mamba cache blocks` — lower `--max-num-seqs`

**Tunnel returns 502**
- Cloudflared is running but can't reach vLLM.
- If using `localhost` in tunnel config, cloudflared may resolve to IPv6 `[::1]` but vLLM only listens on IPv4. Use `127.0.0.1` instead.
- Run `check-status.sh` to diagnose.

**VAST instance restarted**
- Both vLLM and cloudflared run as background processes (not systemd services).
- Re-run `./launch-vllm.sh` then the cloudflared start portion of `setup-vast-tunnel.sh`.
  (The tunnel and DNS already exist, so the script is idempotent.)
