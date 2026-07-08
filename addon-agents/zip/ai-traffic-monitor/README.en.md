# AI Traffic Monitor (`ai-traffic-monitor`)

> 🌐 [한국어](./README.md) · SeCuardian Addon Agent (pure ADDON, no `emb_` prefix)
> PRD: [../../.docs/PRD-ai-traffic-monitor.md](../../.docs/PRD-ai-traffic-monitor.md)
> Source: [Browser AI-assistant traffic monitoring research](../../.docs/Perplexity-브라우저%20등에서%20자동으로%20연결되는%20AI%20도우미와의%20대화시의%20트래픽.md)

## Overview

Quantifies the **traffic usage (bytes/packets), not conversation content**, of browser-connected AI
assistants (Perplexity, Gemini, ChatGPT, Claude, Copilot) via CLI tools. For Shadow-AI usage observability.

- `agent_type`: `service` · governance: `human_approval_required=true`, `audit_level=high`
- No dedicated screen → used via AI Assistant Q&A / capability routing
- Mount: `/api/addon/ai-traffic-monitor/...`

## Architecture (wraps the 3-tier CLI approach)

| Layer | Tool | Purpose |
|-------|------|---------|
| Interface cumulative | `vnstat --json` | daily/monthly/total usage |
| Per-process live | `nethogs -t` | browser process send/recv |
| Destination aggregate | `dig` → `tcpdump` → `tshark` | AI-IP HTTPS bytes/packets |

All execution uses **shell=False + internally assembled argv**, a binary allowlist
(`dig getent vnstat nethogs tcpdump tshark`), and input validation (regex, `ipaddress`, path sandboxing).
Missing tools return **503 + install hint**.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/status` | login | Tool availability + config summary |
| GET | `/domains` | login | AI domain catalog |
| POST | `/resolve` | login | Domain → IP set |
| GET | `/usage` | login | vnstat cumulative usage |
| POST | `/snapshot` | supervisor/admin | nethogs N-sec process snapshot |
| POST | `/capture` | supervisor/admin | AI-IP tcpdump N-sec → tshark aggregate |
| POST | `/analyze` | supervisor/admin | Re-aggregate an existing pcap |
| GET | `/config` | supervisor/admin | Env-var config |

## Environment (all optional)

| Key | Default | Description |
|-----|---------|-------------|
| `AITM_INTERFACE` | `eth0` | Target NIC |
| `AITM_DOMAINS` | (built-in catalog) | CSV override |
| `AITM_CAPTURE_DIR` | `/tmp/ai-traffic` | pcap dir (sandbox root) |
| `AITM_MAX_CAPTURE_SEC` | `60` | Max capture seconds |
| `AITM_MAX_SNAPSHOT_SEC` | `30` | Max snapshot seconds |

> Config location: full comments live in repo-root `.env.example`. `.env.local` (host-direct run) sets
> `en0`; `.env.dev`/`.env.staging`/`.env.prod` (Docker) set `eth0` — minimal application. Add the
> optional vars only when needed (unset = code default).

## Deploy / Run

1. Agent Management → New Agent → **ZIP Upload** → `zip/ai-traffic-monitor.zip`
2. Hot-deployed instantly at `/api/addon/ai-traffic-monitor`

> ⚠️ `snapshot`/`capture` need raw-packet access → **root** or `CAP_NET_RAW`/`CAP_NET_ADMIN`.
> Grant the capability (or host network mode) for container deployments.

## API Examples

```bash
curl -s /api/addon/ai-traffic-monitor/status
# → {"tools":{"dig":true,"tcpdump":true,"vnstat":false,...},"all_available":false,...}

curl -s -X POST /api/addon/ai-traffic-monitor/resolve \
  -H 'Content-Type: application/json' -d '{"domains":["claude.ai"]}'
# → {"resolved":{"claude.ai":["160.79.104.10"]},"unique_ips":[...],"ip_count":1}

curl -s -X POST /api/addon/ai-traffic-monitor/capture \
  -H 'Content-Type: application/json' -d '{"seconds":30}'
# → {"packets":842,"bytes":1183920,"pcap":"/tmp/ai-traffic/aitm-eth0-30s-9ips.pcap",...}
```

## Test

```bash
python3 test/impl/51/run_test.py    # run from repo root → 10/10 PASS
```

**Integration test**: `./ITManually.sh 13` (or interactive menu #13) — checks the
`status`/`domains`/`resolve`/`usage` APIs (after zip upload) plus Frontend (AI Assistant) routing.
Preview: `DRYRUN=1 ./ITManually.sh 13`. Guide: [.docs/ITManually.md](../../../.docs/ITManually.md).

## Troubleshooting

| Symptom | Cause / Fix |
|---------|-------------|
| `/usage` 503 | `vnstat` missing/unconfigured → install, then `vnstat --add -i <iface>` + start daemon (Linux `systemctl enable --now vnstat`, macOS `brew services start vnstat`). Takes minutes to accumulate. A missing DB/daemon returns 503 (graceful), not 502 |
| `/chat` query calls a nonexistent path (e.g. `/interface/eth0/usage`), returns 404 | Ollama guessed a REST-conventional path because it didn't see the query param (`?interface=`) — a platform-level defect in orchestrator `_openapi_endpoint_lines`, fixed in impl/54. Resolved by a backend restart (no addon re-upload needed) |
| `/capture` no pcap | Insufficient root/capability, or wrong interface (check `/status`) |
| resolve returns no IPs | CDN/DoH environment — retry or adjust `AITM_DOMAINS` |

## Next steps (PRD §7)

- tshark aggregation → Prometheus textfile exporter (`ai_domain_bytes_total{domain=}`) → Grafana
- ring-buffer long captures, DNS+TLS SNI correlation
- `-front.tsx` per-domain usage dashboard
