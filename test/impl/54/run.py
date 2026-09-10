"""impl/54 — E10 패키징 4종(logto/istio/wireproxy/observability 모니터) 시험 하네스.

본 제품 SeCuardian 라우터 → marketplace-assets/security ADDON 이식본 검증.
외부 서비스는 미기동 전제 — 엔드포인트가 크래시 없이 UNREACHABLE/DOWN/503 으로 우아하게 저하하는지 확인.
실행: .venv/bin/python test/impl/54/run.py
"""
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
SEC = ROOT / "marketplace-assets" / "security"
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.core.deps import get_current_user  # noqa: E402

PASS, FAIL = [], []


def check(tc, cond, detail=""):
    (PASS if cond else FAIL).append(tc)
    print(f"  [{'PASS' if cond else 'FAIL'}] {tc}{(' — ' + detail) if detail else ''}")


def load(key):
    p = SEC / key / f"{key}-app.py"
    spec = importlib.util.spec_from_file_location(f"addon_{key.replace('-', '_')}", str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def client(module, key):
    app = FastAPI()
    app.include_router(module.router, prefix=f"/api/addon/{key}")
    app.dependency_overrides[get_current_user] = lambda: {"role": "admin", "username": "t"}
    return TestClient(app)


AGENTS = ["logto-monitor", "istio-mtls", "wireproxy-ztna", "observability-monitor"]


def main():
    print("== TC-54-00 로드/스키마 ==")
    mods = {}
    for k in AGENTS:
        try:
            mods[k] = load(k)
            has_router = hasattr(mods[k], "router")
            meta = json.loads((SEC / k / f"{k}-meta.json").read_text(encoding="utf-8"))
            meta_ok = meta.get("agent_type") == "service" and meta.get("agent_key") == k and "capabilities" in meta
            src = (SEC / k / f"{k}-app.py").read_text().splitlines()
            no_future = not any(ln.strip().startswith("from __future__ import") for ln in src)
            check(f"{k}: router+meta+no-future", has_router and meta_ok and no_future,
                  ("meta" if not meta_ok else "") + ("" if no_future else " __future__"))
        except Exception as exc:  # noqa: BLE001
            check(f"{k}: load", False, str(exc)[:150])

    # TC-54-01 logto — status 외부미기동 503 / config 200
    print("== TC-54-01 logto-monitor ==")
    c = client(mods["logto-monitor"], "logto-monitor")
    r = c.get("/api/addon/logto-monitor/status")
    check("logto: status graceful(503/200)", r.status_code in (200, 503), str(r.status_code))
    check("logto: config 200", c.get("/api/addon/logto-monitor/config").status_code == 200)

    # TC-54-02 istio — status UNREACHABLE(200) / mtls / config
    print("== TC-54-02 istio-mtls ==")
    c = client(mods["istio-mtls"], "istio-mtls")
    r = c.get("/api/addon/istio-mtls/status")
    check("istio: status graceful", r.status_code == 200 and r.json().get("status") in ("UP", "DOWN", "UNREACHABLE"), str(r.json()))
    check("istio: mtls 200 STRICT", c.get("/api/addon/istio-mtls/mtls").json()["peer_authentication"]["mode"] == "STRICT")
    check("istio: config 200", c.get("/api/addon/istio-mtls/config").status_code == 200)

    # TC-54-03 wireproxy — status graceful / config
    print("== TC-54-03 wireproxy-ztna ==")
    c = client(mods["wireproxy-ztna"], "wireproxy-ztna")
    r = c.get("/api/addon/wireproxy-ztna/status")
    check("wireproxy: status graceful", r.status_code == 200 and r.json().get("status") in ("UP", "UNREACHABLE"), str(r.json().get("status")))
    check("wireproxy: config 200", c.get("/api/addon/wireproxy-ztna/config").status_code == 200)

    # TC-54-04 observability — status/mttd flow
    print("== TC-54-04 observability-monitor ==")
    c = client(mods["observability-monitor"], "observability-monitor")
    r = c.get("/api/addon/observability-monitor/status")
    check("obs: status PARTIAL/UP", r.status_code == 200 and "services" in r.json(), str(r.status_code))
    # MTTD flow: alert → response → stats
    a = c.post("/api/addon/observability-monitor/mttd/alert", json={"alert_id": "A1", "attack_time": "2026-09-10T00:00:00", "source": "wazuh"})
    check("obs: mttd/alert 202", a.status_code == 202 and a.json()["event"]["mttd_seconds"] is not None)
    rp = c.post("/api/addon/observability-monitor/mttd/response", json={"alert_id": "A1"})
    check("obs: mttd/response MTTR 계산", rp.status_code == 202 and rp.json().get("updated", {}).get("mttr_seconds") is not None, str(rp.json())[:120])
    st = c.get("/api/addon/observability-monitor/mttd").json()
    check("obs: mttd 집계 total_alerts>=1", st["total_alerts"] >= 1 and st["mttd"]["sample_count"] >= 1)
    cl = c.request("DELETE", "/api/addon/observability-monitor/mttd")
    check("obs: mttd DELETE 초기화", cl.status_code == 200 and cl.json()["cleared"] >= 1)

    print(f"\n=== RESULT: {len(PASS)} PASS / {len(FAIL)} FAIL ===")
    if FAIL:
        print("FAILED:", FAIL)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
