# Linux 하드닝 감사자 — Worker 설치 가이드 / Worker Install Guide

> 이 에이전트는 외부 worker(Ansible + 하드닝 플레이북)가 감사 결과를 push 해야 동작합니다.

---

## 1. Worker 개요

- **도구 이름**: [Ansible](https://docs.ansible.com/) 2.15+ (GPL-3.0, CLI 도구 — 내부 사용 OK) + SeCuardian 하드닝 플레이북 (`deploy/ansible/playbooks/linux_hardening.yml`, `audit_hardening.yml`)
- **역할**: SSH/커널/패키지/감사 로그 등 CIS 기반 Linux 서버 하드닝 적용 및 준수 감사. 감사 결과를 JSON 으로 SeCuardian 에 보고합니다.
- **연결 방식**: `audit_hardening.yml` 의 `uri` 태스크 → `POST http://<SeCuardian>:8200/api/addon/hardening-auditor/report` (JWT 없음, `HARDENING_WEBHOOK_ENABLED=true` 로 게이트)

## 2. 요구 사항

| 항목 | 조건 |
|------|------|
| 제어 노드 | Python 3.10+, `pip install ansible` 또는 `uv tool install ansible` |
| 대상 서버 | SSH 접근 + sudo 권한 (Ubuntu 22.04 / RHEL 9 계열) |
| 인벤토리 | `deploy/ansible/inventory/hosts.yml` (그룹 `secuardian_servers`) |
| 네트워크 | 제어 노드 → SeCuardian 8200 도달 가능 |

## 3. 설치·실행 (SeCuardian 저장소 기준)

```bash
pip install ansible
cd deploy/ansible
# 인벤토리 편집: inventory/hosts.yml 에 대상 호스트 등록

# 1) 문법 검사 / dry-run
ansible-playbook -i inventory/hosts.yml playbooks/linux_hardening.yml --syntax-check
ansible-playbook -i inventory/hosts.yml playbooks/linux_hardening.yml --check --diff
# 2) 적용
ansible-playbook -i inventory/hosts.yml playbooks/linux_hardening.yml
# 3) 감사만
ansible-playbook -i inventory/hosts.yml playbooks/audit_hardening.yml
# 4) 감사 + SeCuardian 보고 (Addon 경로 지정)
ansible-playbook -i inventory/hosts.yml playbooks/audit_hardening.yml \
  -e report_to_secuardian=true \
  -e secuardian_api_url=http://<SECUARDIAN_HOST>:8200 \
  -e secuardian_report_path=/api/addon/hardening-auditor/report
```

> `audit_hardening.yml` 기본 보고 경로는 내장판 `/api/hardening/report` 입니다. 플레이북의 `uri.url` 을
> `"{{ secuardian_api_url }}{{ secuardian_report_path | default('/api/addon/hardening-auditor/report') }}"` 로 수정하거나
> 위처럼 `-e` 로 경로를 넘기세요. 보고 조건에 `secuardian_api_token` 이 있으면 빈 값이 아니어야 합니다(Addon 은 토큰을 검증하지 않음).

### 독립 사용 (저장소 없이) — 직접 보고

```bash
curl -s -X POST http://localhost:8200/api/addon/hardening-auditor/report -H "Content-Type: application/json" \
  -d '{"hostname":"web-01","audited_at":"2026-08-27T00:00:00Z","overall_pass":true,
       "checks":[{"id":"ssh_root_login","pass":true},{"id":"password_max_days","pass":true}]}'
```

## 4. 에이전트 연결 (SeCuardian-Basic `.env`)

```bash
HARDENING_WEBHOOK_ENABLED=true      # 필수 — false 면 POST /report 가 403
HARDENING_REPORTS_MAX=100           # 선택 — 인메모리 보관 최대 건수
HARDENING_PLAYBOOK_DIR=deploy/ansible   # 선택 — /status 의 run_hints 경로 표시용
```

## 5. 동작 확인

```bash
TOKEN=<SeCuardian JWT>
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8200/api/addon/hardening-auditor/status
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8200/api/addon/hardening-auditor/reports?limit=5"
```

| 증상 | 조치 |
|------|------|
| 403 `hardening webhook disabled` | `HARDENING_WEBHOOK_ENABLED=true` |
| 플레이북 보고 스킵 | `report_to_secuardian=true` 및 `secuardian_api_token` 비어있지 않은지 확인 |
| 재시작 후 보고서 소실 | 인메모리 저장소 — 장기 보존은 별도 SIEM 전송 권장 |
