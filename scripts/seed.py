#!/usr/bin/env python3
"""시드 스크립트 — 기본 설정 + 테스트 데이터 삽입.

Usage:
    uv run python scripts/seed.py
    make seed

포함 내용:
  - tbl_settings: LLM 기본값 (ollama, claude 모델명, setup_completed=false)

  - tbl_users: supervisor(secuardian/Secu1234!) + admin(test-admin/Admin1234!) + user(test-user/User1234!)
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings as _settings
from app.core.security import hash_password
from app.db import execute_write, fetch_one, run_migrations, apply_column_migrations, _IS_SQLITE, _PH


# env var / .env.* 파일 값 우선 반영 — 하드코딩 대신 settings.* 사용
SETTINGS = [
    ("orchestrator_model",  _settings.orchestrator_model, "Orchestrator LLM 모델"),
    ("domain_agent_model",  _settings.domain_agent_model, "Domain Agent LLM 모델"),
    ("ollama_base_url",     _settings.ollama_base_url,    "Ollama 서버 주소"),
    ("ollama_model",        _settings.ollama_model,       "Ollama 기본 모델"),
    ("fallback_enabled",    "true",                       "LLM Fallback 활성화"),
    ("setup_completed",     "false",                      "Setup Wizard 완료"),
]

AGENT_CONFIGS: list = [
    # Phase 1 — Foundation
    # vasca-cve: VASCA CVE 스캔 에이전트 (E07 T07-1) — L2 Endpoint / vuln_scan 인텐트
    ("vasca-cve", "VASCA CVE Scanner", 1, "security", 70),
    # Phase 2 — Visibility & Automation (E09~E15) ADDON 에이전트
    ("cilium-netpol", "Cilium Network Policy", 1, "security", 71),   # E09 L3 Network
    ("teler-ids",     "teler HTTP IDS",         1, "security", 72),   # E11 L4 Application
    ("shuffle-soar",  "Shuffle SOAR",           1, "security", 73),   # E13 L5 Detection
    ("neosync-dlp",   "Neosync DLP",            1, "security", 74),   # E14 L4 Data
    ("otel-collector","OpenTelemetry Collector", 1, "security", 75),  # E15 Cross-cutting
    # Phase 3 — Advanced Defense (E17~E22) ADDON 에이전트
    ("teleport-pam",       "Teleport PAM",              1, "security", 76),  # E17 L1 Identity
    ("velociraptor-dfir",  "Velociraptor DFIR",          1, "security", 77),  # E18 L6 Forensics
    ("ai-redteam",         "AI Red Team ⚠️ Isolated",   0, "security", 78),  # E19 L6 비활성(격리 필수)
    ("isms-p-evidence",    "ISMS-P Evidence Collector",  1, "security", 79),  # E22 Cross-cutting
    # Phase 4 — BehaviorNotiService + VASCA v2
    ("behavior-noti",     "BehaviorNotiService C++",    1, "security", 80),  # E16 L5 Detection
    # Phase 5 — AI Defense (E20, E21)
    ("agentic-soc",       "Agentic SOC Platform",       1, "security", 81),  # E21 L5 Detection
    ("ai-eval-gate",      "AI Security Eval Gate ⚠️",   0, "security", 82),  # E20 기본 비활성
]

# 에이전트 설명 — 에이전트 관리 화면 이름 hover 툴팁으로 노출 (tbl_agent_config.description)
AGENT_DESCRIPTIONS: dict = {
    "vasca-cve": "호스트·컨테이너 이미지의 CVE 취약점을 스캔하고 결과를 수집·보고하는 VASCA 취약점 스캔 에이전트입니다.",
    "cilium-netpol": "Cilium eBPF 네트워크 정책과 Hubble 플로우 이벤트를 모니터링하는 마이크로세그멘테이션 에이전트입니다.",
    "teler-ids": "teler HTTP 침입 탐지(IDS) 알림을 웹훅으로 수신하고 조회·통계를 제공하는 에이전트입니다.",
    "shuffle-soar": "Shuffle SOAR 워크플로를 트리거하고 실행 결과를 수집하는 보안 자동화 에이전트입니다.",
    "neosync-dlp": "Neosync DLP 파이프라인 상태를 모니터링하고 Job 실행을 관리하는 데이터 보호 에이전트입니다.",
    "otel-collector": "OpenTelemetry Collector의 헬스·파이프라인·메트릭 상태를 조회하는 관측성 에이전트입니다.",
    "teleport-pam": "Teleport 특권 접근(PAM) 감사 이벤트를 수집하고 활성 세션·사용자를 조회하는 에이전트입니다.",
    "velociraptor-dfir": "Velociraptor 기반 엔드포인트 포렌식 헌팅과 아티팩트 수집을 수행하는 DFIR 에이전트입니다.",
    "ai-redteam": "PyRIT·SkillSpector로 LLM 탈옥·프롬프트 인젝션 등 적대적 스캔을 수행하는 AI 레드팀 에이전트입니다.",
    "isms-p-evidence": "ISMS-P 인증 대응을 위한 감사 증거를 자동 수집·보고하는 컴플라이언스 에이전트입니다.",
    "behavior-noti": "호스트 에이전트(C++)의 이상 행위 이벤트를 웹훅으로 수신·분석하는 행위 기반 알림 에이전트입니다.",
    "agentic-soc": "보안 에이전트들을 A2A로 오케스트레이션하고 인시던트 트리아지·플레이북을 실행하는 Agentic SOC 플랫폼입니다.",
    "ai-eval-gate": "PyRIT 등 AI 보안 평가 결과를 수집하고 배포 게이트 PASS/FAIL을 판정하는 평가 게이트 에이전트입니다.",
}

# 영문 설명 — UI '언어' 선택(en) 시 노출 (tbl_agent_config.description_en)
AGENT_DESCRIPTIONS_EN: dict = {
    "vasca-cve": "VASCA vulnerability scanner agent that scans hosts and container images for CVEs and collects/reports the results.",
    "cilium-netpol": "Microsegmentation agent that monitors Cilium eBPF network policies and Hubble flow events.",
    "teler-ids": "Agent that receives teler HTTP intrusion detection (IDS) alerts via webhook and provides queries and statistics.",
    "shuffle-soar": "Security automation agent that triggers Shuffle SOAR workflows and collects execution results.",
    "neosync-dlp": "Data protection agent that monitors Neosync DLP pipeline status and manages job runs.",
    "otel-collector": "Observability agent that queries OpenTelemetry Collector health, pipelines, and metrics.",
    "teleport-pam": "Agent that collects Teleport privileged access (PAM) audit events and lists active sessions and users.",
    "velociraptor-dfir": "DFIR agent that performs Velociraptor-based endpoint forensic hunting and artifact collection.",
    "ai-redteam": "AI red-team agent that runs adversarial scans such as LLM jailbreak and prompt injection with PyRIT and SkillSpector.",
    "isms-p-evidence": "Compliance agent that automatically collects and reports audit evidence for ISMS-P certification.",
    "behavior-noti": "Behavior-based alerting agent that receives and analyzes anomalous-behavior events from the C++ host agent via webhook.",
    "agentic-soc": "Agentic SOC platform that orchestrates security agents over A2A and runs incident triage and playbooks.",
    "ai-eval-gate": "Evaluation gate agent that collects AI security evaluation results (e.g. PyRIT) and issues a deploy-gate PASS/FAIL verdict.",
}

# 기본 비활성 에이전트의 사유 — 에이전트 관리 화면 ⚠️ 툴팁으로 노출
DISABLED_REASONS: dict = {
    "ai-redteam": (
        "AI Red Team(pentagi)은 공격 도구를 포함하고 있어 운영망과 분리된 "
        "격리 환경에서만 실행할 수 있습니다. 격리 환경 구성 후 활성화하세요."
    ),
    "ai-eval-gate": (
        "AI 보안 평가 게이트는 평가 대상 LLM과 평가 파이프라인 구성이 필요해 "
        "기본 비활성 상태입니다. 구성 완료 후 활성화하세요."
    ),
}

# 영문 사유 — UI '언어' 선택(en) 시 노출 (tbl_agent_config.disabled_reason_en)
DISABLED_REASONS_EN: dict = {
    "ai-redteam": (
        "AI Red Team (pentagi) includes offensive tooling and can only run in an "
        "isolated environment separated from the production network. Enable it after "
        "the isolation environment is in place."
    ),
    "ai-eval-gate": (
        "The AI security evaluation gate is disabled by default because it requires "
        "a target LLM and an evaluation pipeline. Enable it once the configuration is complete."
    ),
}

TEST_USERS = [
    ("secuardian",  "supervisor",   "Secu1234!",  "supervisor"),
    ("test-admin",  "테스트관리자", "Admin1234!", "admin"),
    ("test-user",   "테스트사용자", "User1234!",  "user"),
]


async def main() -> None:
    # 스키마 보장 (아직 없으면 생성) — 컬럼 ALTER 먼저, 그 다음 init+seed (main.py lifespan 과 동일 순서)
    await apply_column_migrations()
    await run_migrations()

    _conflict = "OR IGNORE" if _IS_SQLITE else ""
    _on_conflict = "" if _IS_SQLITE else "ON CONFLICT DO NOTHING"

    # tbl_settings
    for key, value, desc in SETTINGS:
        await execute_write(
            f"INSERT {_conflict} INTO tbl_settings (key, value, description) VALUES ({_PH},{_PH},{_PH}) {_on_conflict}",
            (key, value, desc),
        )
        print(f"[seed] settings: {key} = {value}")

    # tbl_agent_config
    for agent_key, agent_name, is_enabled, nav_group, sort_order in AGENT_CONFIGS:
        await execute_write(
            f"INSERT {_conflict} INTO tbl_agent_config "
            f"(agent_key, agent_name, is_enabled, nav_group, sort_order) VALUES ({_PH},{_PH},{_PH},{_PH},{_PH}) {_on_conflict}",
            (agent_key, agent_name, is_enabled, nav_group, sort_order),
        )
        print(f"[seed] agent_config: {agent_key}")

    # 에이전트 설명 (이름 마우스 오버 툴팁) — 기존 행에도 반영 (멱등 UPDATE)
    for agent_key, desc in AGENT_DESCRIPTIONS.items():
        await execute_write(
            f"UPDATE tbl_agent_config SET description = {_PH} WHERE agent_key = {_PH}",
            (desc, agent_key),
        )
        print(f"[seed] description: {agent_key}")

    # 영문 설명 (언어=en 선택 시 노출) — 멱등 UPDATE
    for agent_key, desc_en in AGENT_DESCRIPTIONS_EN.items():
        await execute_write(
            f"UPDATE tbl_agent_config SET description_en = {_PH} WHERE agent_key = {_PH}",
            (desc_en, agent_key),
        )
        print(f"[seed] description_en: {agent_key}")

    # 비활성 사유 (⚠️ 마우스 오버 툴팁) — 기존 행에도 반영 (멱등 UPDATE)
    for agent_key, reason in DISABLED_REASONS.items():
        await execute_write(
            f"UPDATE tbl_agent_config SET disabled_reason = {_PH} WHERE agent_key = {_PH}",
            (reason, agent_key),
        )

    # 영문 사유 (언어=en 선택 시 노출) — 멱등 UPDATE
    for agent_key, reason_en in DISABLED_REASONS_EN.items():
        await execute_write(
            f"UPDATE tbl_agent_config SET disabled_reason_en = {_PH} WHERE agent_key = {_PH}",
            (reason_en, agent_key),
        )
        print(f"[seed] disabled_reason: {agent_key}")

    # tbl_users
    for user_id, username, password, role in TEST_USERS:
        row = await fetch_one(f"SELECT 1 FROM tbl_users WHERE user_id={_PH}", (user_id,))
        if row:
            print(f"[seed] users: {user_id} (이미 존재, 건너뜀)")
        else:
            await execute_write(
                f"INSERT INTO tbl_users (user_id, username, password, role) VALUES ({_PH},{_PH},{_PH},{_PH})",
                (user_id, username, hash_password(password), role),
            )
            print(f"[seed] users: {user_id} ({role}) 생성")

    print("\n[seed] 완료!")
    print("  supervisor: secuardian / Secu1234!")
    print("  admin:      test-admin / Admin1234!")
    print("  user:       test-user  / User1234!")


if __name__ == "__main__":
    asyncio.run(main())
