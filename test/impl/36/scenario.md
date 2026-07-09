# 시험 시나리오 — 자산 디렉터리 재구성 (§7.6.1-7, impl/38 · 물리 test/impl/36)

배경(PRD §7.6.1-7, 사용자 요구 2026-07-09): SeCMP 의 모든 자산 소스를
`marketplace-assets/<카테고리>/` 로 일원화하고 `addon-agents/{zip,_templates}` 를 폐지한다.

- **security/** (13): vasca-cve 등 — 기존 유지
- **builtin/** (5): marketplace·workflow·rag·playground·guardrails
- **addon/** (6): 스캐폴드 템플릿 Board·RagAgent·ServiceAgent·ShellAgent·ToolProxyAgent
- **utilities/** (6): UserManager·server-shell·ai-traffic-monitor·caddy-proxy·grafana-dashboard·truffle-scan

`router_addon_agent.py` 템플릿 조회 기준 경로 → `marketplace-assets/addon` (fallback 제거).

| ID | 입력 | 기대 |
|----|------|------|
| TC-36-01 | 디렉터리 구조 | addon-agents/{zip,_templates} 부재, marketplace-assets/{security,builtin,addon,utilities} 각 13/5/6/6 |
| TC-36-02 | 각 카테고리 패키지 | 디렉터리 + `{key}.zip` 쌍 존재, emb_ prefix 0건 |
| TC-36-03 | GET templates/list | addon/ 5종(Board·RagAgent·ServiceAgent·ShellAgent·ToolProxyAgent) — utilities/builtin 미포함 |
| TC-36-04 | GET templates/download/Board | 200 zip; utilities 의 UserManager 는 404 |
| TC-36-05 | POST scaffold (app/service/tool-proxy/rag/shell) | 200 — `_find_template_dir` marketplace-assets/addon 조회 |
| TC-36-06 | guardrails.zip(builtin) | data/guardrails/*.json 구조 보존 |
| TC-36-07 | 회귀 | impl/34(개정)·impl/35(개정)·impl/1·impl/2 PASS, seed_security 13종 |
