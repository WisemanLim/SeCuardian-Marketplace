#!/usr/bin/env python3
"""보안 내장 에이전트 → 자산 카탈로그 시드 스크립트 (§7.6.1) — 기반 시드(seed.py)에서 분리.

Usage:
    uv run python scripts/seed_security.py
    make seed-security

포함 내용:
  - marketplace_assets: 보안 에이전트 13종 (kind=agent, category=security, source=local)
  - marketplace_asset_blobs: marketplace-assets/security/{key}.zip 블롭 (설치 시 hot-deploy)

설치는 기존 계약 그대로 — POST /api/marketplace/install/{asset_key} 가 tbl_agent_config upsert
(nav_group='marketplace') + zip 블롭 hot-deploy 를 수행해 '내장 에이전트' 통합 탭에 편입된다.
기반 설정·테스트 계정은 `make seed`(scripts/seed.py) 담당.
"""
import asyncio
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings as _settings
from app.db import execute_insert, execute_write, fetch_one, run_migrations, apply_column_migrations, _PH

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "marketplace-assets" / "security"

# (asset_key, name, name_en, ko 설명, en 설명) — asset_key = config key (§7.6.1-6: prefix 없음)
# (설치 시 tbl_agent_config.agent_key 로 upsert — Orchestrator 인텐트 라우팅 키와 일치)
SECURITY_ASSETS: list = [
    ("vasca-cve", "VASCA CVE Scanner", "VASCA CVE Scanner",
     "호스트·컨테이너 이미지의 CVE 취약점을 스캔하고 결과를 수집·보고하는 VASCA 취약점 스캔 에이전트입니다.",
     "VASCA vulnerability scanner agent that scans hosts and container images for CVEs and collects/reports the results."),
    ("cilium-netpol", "Cilium Network Policy", "Cilium Network Policy",
     "Cilium eBPF 네트워크 정책과 Hubble 플로우 이벤트를 모니터링하는 마이크로세그멘테이션 에이전트입니다.",
     "Microsegmentation agent that monitors Cilium eBPF network policies and Hubble flow events."),
    ("teler-ids", "teler HTTP IDS", "teler HTTP IDS",
     "teler HTTP 침입 탐지(IDS) 알림을 웹훅으로 수신하고 조회·통계를 제공하는 에이전트입니다.",
     "Agent that receives teler HTTP intrusion detection (IDS) alerts via webhook and provides queries and statistics."),
    ("shuffle-soar", "Shuffle SOAR", "Shuffle SOAR",
     "Shuffle SOAR 워크플로를 트리거하고 실행 결과를 수집하는 보안 자동화 에이전트입니다.",
     "Security automation agent that triggers Shuffle SOAR workflows and collects execution results."),
    ("neosync-dlp", "Neosync DLP", "Neosync DLP",
     "Neosync DLP 파이프라인 상태를 모니터링하고 Job 실행을 관리하는 데이터 보호 에이전트입니다.",
     "Data protection agent that monitors Neosync DLP pipeline status and manages job runs."),
    ("otel-collector", "OpenTelemetry Collector", "OpenTelemetry Collector",
     "OpenTelemetry Collector의 헬스·파이프라인·메트릭 상태를 조회하는 관측성 에이전트입니다.",
     "Observability agent that queries OpenTelemetry Collector health, pipelines, and metrics."),
    ("teleport-pam", "Teleport PAM", "Teleport PAM",
     "Teleport 특권 접근(PAM) 감사 이벤트를 수집하고 활성 세션·사용자를 조회하는 에이전트입니다.",
     "Agent that collects Teleport privileged access (PAM) audit events and lists active sessions and users."),
    ("velociraptor-dfir", "Velociraptor DFIR", "Velociraptor DFIR",
     "Velociraptor 기반 엔드포인트 포렌식 헌팅과 아티팩트 수집을 수행하는 DFIR 에이전트입니다.",
     "DFIR agent that performs Velociraptor-based endpoint forensic hunting and artifact collection."),
    ("ai-redteam", "AI Red Team ⚠️ Isolated", "AI Red Team ⚠️ Isolated",
     "PyRIT·SkillSpector로 LLM 탈옥·프롬프트 인젝션 등 적대적 스캔을 수행하는 AI 레드팀 에이전트입니다. "
     "⚠️ 운영망과 분리된 격리 환경에서만 실행하세요.",
     "AI red-team agent that runs adversarial scans such as LLM jailbreak and prompt injection with PyRIT and SkillSpector. "
     "⚠️ Run only in an isolated environment separated from the production network."),
    ("isms-p-evidence", "ISMS-P Evidence Collector", "ISMS-P Evidence Collector",
     "ISMS-P 인증 대응을 위한 감사 증거를 자동 수집·보고하는 컴플라이언스 에이전트입니다.",
     "Compliance agent that automatically collects and reports audit evidence for ISMS-P certification."),
    ("behavior-noti", "BehaviorNotiService C++", "BehaviorNotiService C++",
     "호스트 에이전트(C++)의 이상 행위 이벤트를 웹훅으로 수신·분석하는 행위 기반 알림 에이전트입니다.",
     "Behavior-based alerting agent that receives and analyzes anomalous-behavior events from the C++ host agent via webhook."),
    ("agentic-soc", "Agentic SOC Platform", "Agentic SOC Platform",
     "보안 에이전트들을 A2A로 오케스트레이션하고 인시던트 트리아지·플레이북을 실행하는 Agentic SOC 플랫폼입니다.",
     "Agentic SOC platform that orchestrates security agents over A2A and runs incident triage and playbooks."),
    ("ai-eval-gate", "AI Security Eval Gate ⚠️", "AI Security Eval Gate ⚠️",
     "PyRIT 등 AI 보안 평가 결과를 수집하고 배포 게이트 PASS/FAIL을 판정하는 평가 게이트 에이전트입니다. "
     "⚠️ 평가 대상 LLM·평가 파이프라인 구성 후 사용하세요.",
     "Evaluation gate agent that collects AI security evaluation results (e.g. PyRIT) and issues a deploy-gate PASS/FAIL verdict. "
     "⚠️ Configure a target LLM and evaluation pipeline before use."),
]

_VERSION = "1.0.0"


def _tenant() -> str:
    return _settings.tenant_default_id or "default"


async def main() -> None:
    # 스키마 보장 (아직 없으면 생성) — seed.py 와 동일 순서
    await apply_column_migrations()
    await run_migrations()

    tid = _tenant()
    for asset_key, name, name_en, desc_ko, desc_en in SECURITY_ASSETS:
        zip_path = _ASSETS_DIR / f"{asset_key}.zip"
        raw = zip_path.read_bytes() if zip_path.exists() else b""
        checksum = hashlib.sha256(raw).hexdigest() if raw else ""

        dup = await fetch_one(
            f"SELECT id FROM marketplace_assets WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
            (asset_key, _VERSION, tid),
        )
        if dup:
            # 멱등 갱신 — 설명·거버넌스·checksum 만 동기 (설치 상태 불변)
            await execute_write(
                f"UPDATE marketplace_assets SET name = {_PH}, name_en = {_PH}, description = {_PH}, "
                f"category = 'security', checksum = {_PH}, updated_at = CURRENT_TIMESTAMP "
                f"WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
                (name, name_en, desc_ko, checksum, asset_key, _VERSION, tid),
            )
            print(f"[seed-security] asset (갱신): {asset_key}")
        else:
            await execute_insert(
                f"INSERT INTO marketplace_assets "
                f"(tenant_id, asset_key, version, kind, name, name_en, description, category, "
                f" min_platform_version, governance, required_env, checksum, source) "
                f"VALUES ({','.join([_PH] * 13)})",
                (tid, asset_key, _VERSION, "agent", name, name_en, desc_ko, "security",
                 "0.1.0", "", "", checksum, "local"),
            )
            print(f"[seed-security] asset: {asset_key}")

        # 설치된(설치 이력 있는) 에이전트에는 en 설명을 직접 동기 — marketplace_assets 에는
        # description_en 컬럼이 없어 카탈로그는 ko 설명만 보유(기존 register_asset 계약과 동일)
        await execute_write(
            f"UPDATE tbl_agent_config SET description_en = {_PH} WHERE agent_key = {_PH}",
            (desc_en, asset_key),
        )

        if raw:
            blob = await fetch_one(
                f"SELECT id, checksum FROM marketplace_asset_blobs "
                f"WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
                (asset_key, _VERSION, tid),
            )
            if blob and blob.get("checksum") == checksum:
                print(f"[seed-security]   blob 동일(스킵): {asset_key}.zip")
            else:
                await execute_write(
                    f"DELETE FROM marketplace_asset_blobs WHERE asset_key = {_PH} AND version = {_PH} AND tenant_id = {_PH}",
                    (asset_key, _VERSION, tid),
                )
                await execute_insert(
                    f"INSERT INTO marketplace_asset_blobs (tenant_id, asset_key, version, filename, checksum, blob, uploaded_by) "
                    f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
                    (tid, asset_key, _VERSION, f"{asset_key}.zip", checksum, raw, "seed-security"),
                )
                print(f"[seed-security]   blob 등록: {asset_key}.zip ({len(raw)} bytes)")
        else:
            print(f"[seed-security]   ⚠️ zip 미존재: {zip_path}")

    print(f"\n[seed-security] 완료! 보안 에이전트 자산 {len(SECURITY_ASSETS)}종 카탈로그 등록 (category=security)")
    print("  설치: 에이전트 관리 → 내장 에이전트 탭 → 자산 카탈로그 → 설치")


if __name__ == "__main__":
    asyncio.run(main())
