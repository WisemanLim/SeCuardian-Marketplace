# impl/54 시험 시나리오 — E10 패키징 4종 (본 제품 라우터 → ADDON 이식)

대상: `marketplace-assets/security/` 신규 4종 — SeCuardian 본 제품 내장 라우터를 ADDON 자산으로 이식.
`logto-monitor`(router_logto)·`istio-mtls`(router_istio)·`wireproxy-ztna`(router_wireproxy)·`observability-monitor`(router_observability).
실행: `.venv/bin/python test/impl/54/run.py` (standalone).
전제: 외부 서비스(Logto/Istio/WireProxy/Prometheus) 미기동 — 엔드포인트가 크래시 없이 우아하게 저하해야 함.

| TC | 대상 | 수용 기준 |
|---|---|---|
| TC-54-00 | 4종 공통 | `router` 노출 + meta.json(agent_type=service·agent_key 일치·capabilities) + `from __future__ import` 미사용 |
| TC-54-01 | logto-monitor | status 외부미기동 시 503(우아) 또는 200; config 200 |
| TC-54-02 | istio-mtls | status UNREACHABLE(200); mtls STRICT; config 200 |
| TC-54-03 | wireproxy-ztna | status UNREACHABLE/UP(200); config 200 |
| TC-54-04 | observability-monitor | status services 반환; MTTD 플로우(alert→response MTTR 계산→집계→DELETE 초기화) |

부가: `ruff check` 통과, 4종 `.zip` 패키징, `seed_assets` 자동 발견. 이식 시 config 는 env(os.getenv)로 처리
(marketplace settings 비의존), `__future__` 제거.
