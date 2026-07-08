#!/usr/bin/env python3
"""
Keycloak Realm Provisioning Script — E01 T01-2
# Source: SeCuardian | License: internal | Usage: internal only

Realm 구성:
  - internal-realm  : 내부 직원 (SSO, MFA 강제)
  - partner-realm   : 외부 파트너 (자체 등록 허용, 이메일 검증 필수)
  - service-realm   : 서비스 계정 M2M (이메일 검증 불필요)

사용법:
  python deploy/keycloak/realm_setup.py --dry-run        # 계획만 출력
  python deploy/keycloak/realm_setup.py                  # 실제 적용
  python deploy/keycloak/realm_setup.py --realm internal-realm  # 단일 Realm

환경변수:
  KC_URL                   Keycloak 베이스 URL (기본: http://localhost:8880)
  KEYCLOAK_ADMIN           Admin 계정명 (기본: admin)
  KEYCLOAK_ADMIN_PASSWORD  Admin 비밀번호 (필수)
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

KC_URL = os.environ.get("KC_URL", "http://localhost:8880")
KC_ADMIN_USER = os.environ.get("KEYCLOAK_ADMIN", "admin")
KC_ADMIN_PASSWORD = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "")

# 패스워드 정책: 12자+, 특수문자, 대문자, 숫자, 90일 만료
_USER_PASSWORD_POLICY = (
    "length(12) and specialChars(1) and upperCase(1) and digits(1) "
    "and notUsername(undefined) and forceExpiredPasswordChange(90)"
)
# M2M 서비스 계정: 32자+, 만료 없음 (로테이션은 Vault가 담당)
_SVC_PASSWORD_POLICY = (
    "length(32) and specialChars(1) and upperCase(1) and digits(1)"
)

_BRUTE_FORCE = {
    "bruteForceProtected": True,
    "maxFailureWaitSeconds": 900,
    "minimumQuickLoginWaitSeconds": 60,
    "waitIncrementSeconds": 60,
    "maxDeltaTimeSeconds": 43200,
    "failureFactor": 5,
}

REALMS: list[dict] = [
    {
        "id": "internal-realm",
        "realm": "internal-realm",
        "displayName": "SeCuardian Internal",
        "enabled": True,
        "registrationAllowed": False,
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "verifyEmail": True,
        "resetPasswordAllowed": True,
        "passwordPolicy": _USER_PASSWORD_POLICY,
        "sslRequired": "external",
        **_BRUTE_FORCE,
    },
    {
        "id": "partner-realm",
        "realm": "partner-realm",
        "displayName": "SeCuardian Partners",
        "enabled": True,
        "registrationAllowed": True,
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "verifyEmail": True,
        "resetPasswordAllowed": True,
        "passwordPolicy": _USER_PASSWORD_POLICY,
        "sslRequired": "external",
        **_BRUTE_FORCE,
    },
    {
        "id": "service-realm",
        "realm": "service-realm",
        "displayName": "SeCuardian Services (M2M)",
        "enabled": True,
        "registrationAllowed": False,
        "loginWithEmailAllowed": False,
        "duplicateEmailsAllowed": False,
        "verifyEmail": False,
        "resetPasswordAllowed": False,
        "passwordPolicy": _SVC_PASSWORD_POLICY,
        "sslRequired": "external",
        **_BRUTE_FORCE,
    },
]


def _get_admin_token(client: httpx.Client) -> str:
    resp = client.post(
        f"{KC_URL}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "username": KC_ADMIN_USER,
            "password": KC_ADMIN_PASSWORD,
            "grant_type": "password",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _get_existing_realms(client: httpx.Client, token: str) -> set[str]:
    resp = client.get(
        f"{KC_URL}/admin/realms",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return {r["realm"] for r in resp.json()}


def _apply_realm(
    client: httpx.Client, token: str, config: dict, existing: set[str]
) -> None:
    realm_name = config["realm"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if realm_name in existing:
        resp = client.put(
            f"{KC_URL}/admin/realms/{realm_name}",
            headers=headers,
            json=config,
        )
        resp.raise_for_status()
        print(f"  [UPDATE] {realm_name}")
    else:
        resp = client.post(
            f"{KC_URL}/admin/realms",
            headers=headers,
            json=config,
        )
        resp.raise_for_status()
        print(f"  [CREATE] {realm_name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Keycloak Realm Provisioning — E01 T01-2"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="계획 출력만, 변경 없음",
    )
    parser.add_argument(
        "--realm",
        metavar="REALM",
        help="특정 Realm만 처리 (생략 시 전체)",
    )
    args = parser.parse_args(argv)

    if not KC_ADMIN_PASSWORD:
        print("ERROR: KEYCLOAK_ADMIN_PASSWORD 환경변수 미설정", file=sys.stderr)
        return 1

    target = [r for r in REALMS if not args.realm or r["realm"] == args.realm]
    if not target:
        print(f"ERROR: realm '{args.realm}' 정의 없음", file=sys.stderr)
        return 1

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"Keycloak Realm Setup [{mode}]")
    print(f"  URL  : {KC_URL}")
    print(f"  Admin: {KC_ADMIN_USER}")
    print()

    if args.dry_run:
        for r in target:
            print(f"[PLAN] {r['realm']}")
            print(f"       displayName   : {r['displayName']}")
            print(f"       verifyEmail   : {r['verifyEmail']}")
            print(f"       passwordPolicy: {r['passwordPolicy']}")
            print()
        print("Dry-run complete. No changes made.")
        return 0

    try:
        with httpx.Client(timeout=15) as client:
            token = _get_admin_token(client)
            existing = _get_existing_realms(client, token)
            print(f"기존 Realm: {', '.join(sorted(existing))}")
            print()
            for r in target:
                _apply_realm(client, token, r, existing)
    except httpx.ConnectError as exc:
        print(f"ERROR: Keycloak 연결 실패 — {exc}", file=sys.stderr)
        return 1
    except httpx.HTTPStatusError as exc:
        print(f"ERROR: HTTP {exc.response.status_code} — {exc.response.text}", file=sys.stderr)
        return 1

    print()
    print("완료.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
