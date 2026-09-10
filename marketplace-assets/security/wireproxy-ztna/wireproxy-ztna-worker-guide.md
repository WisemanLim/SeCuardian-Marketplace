# WireProxy ZTNA 모니터 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker 가 기동되어 있어야 완전히 동작합니다. 미기동 시 우아하게 저하됩니다.
> This agent requires an external worker; it degrades gracefully when the worker is down.

---

## 1. Worker 개요

- **도구**: [WireProxy](https://github.com/whyvl/wireproxy) (ISC) — WireGuard 유저스페이스 SOCKS5 프록시
- **역할**: WireProxy SOCKS5 프록시 경유 외부 IP 를 조회해 ZTNA 터널 상태를 판정합니다.
- **포트**: `25344`(SOCKS5, 로컬 전용 권장)
- **에이전트 설정 방식**: 환경변수(`os.getenv`) — SeCuardian-Basic `.env.*` 또는 compose `environment` 에 선언

## 2. 환경변수 (`optional_env`)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `WIREPROXY_SOCKS5_HOST` | SOCKS5 바인드 호스트 | `127.0.0.1` |
| `WIREPROXY_SOCKS5_PORT` | SOCKS5 포트 | `25344` |

## 3. 설치 (독립 설치 예시)

```bash
# 1) 설정 — WireGuard 키/엔드포인트는 시크릿 저장소에서 주입
cat > wireproxy.conf <<'CONF'
[Interface]
PrivateKey = <WIREGUARD_PRIVATE_KEY>
Address = 10.0.0.2/32
DNS = 1.1.1.1
[Peer]
PublicKey = <WIREGUARD_SERVER_PUBLIC_KEY>
Endpoint = <WIREGUARD_SERVER_ENDPOINT>
AllowedIPs = 0.0.0.0/0
[Socks5]
BindAddress = 127.0.0.1:25344
CONF
# 2) 실행 (바이너리 또는 컨테이너)
docker run -d --name wireproxy -p 127.0.0.1:25344:25344 \
  -v $PWD/wireproxy.conf:/etc/wireproxy/config:ro ghcr.io/whyvl/wireproxy:latest
curl -s --socks5-hostname 127.0.0.1:25344 http://ifconfig.me/ip
# 3) API venv 에 SOCKS 지원 (httpx[socks])
uv pip install 'httpx[socks]'
```

## 4. 에이전트 엔드포인트 (`/api/addon/wireproxy-ztna`)

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /status` | 프록시 경유 외부 IP (UP/UNREACHABLE) |
| `GET /config` | SOCKS5 주소·필요 시크릿 목록 |

## 5. 미기동 시 동작

WireProxy 미기동 또는 `httpx[socks]` 미설치 시 `/status` 는 `UNREACHABLE` 로 정상 응답합니다.

## 6. 확인

```bash
curl -s -H "Authorization: Bearer <token>" http://localhost:8200/api/addon/wireproxy-ztna/status
```
