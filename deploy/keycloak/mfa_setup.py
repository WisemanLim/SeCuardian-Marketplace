#!/usr/bin/env python3
"""Keycloak MFA 활성화 스크립트 — E01 T01-4.

internal-realm · partner-realm에 TOTP Required Action을 활성화한다.
service-realm은 M2M 계정 전용이므로 MFA 적용 제외.

사용법:
    KC_URL=http://localhost:8880 \\
    KEYCLOAK_ADMIN=admin \\
    KEYCLOAK_ADMIN_PASSWORD=<pw> \\
    uv run python deploy/keycloak/mfa_setup.py [옵션]

옵션:
    --dry-run          실제 변경 없이 예정 작업만 출력
    --realm REALM      단일 Realm 지정 (기본: internal-realm partner-realm 전부)
    --enable-webauthn  WebAuthn Required Action 추가 활성화 (Chrome/Safari 지원)
"""
from __future__ import annotations

import argparse
import os
import sys

import httpx

KC_URL = os.environ.get("KC_URL", "http://localhost:8880")
KC_ADMIN_USER = os.environ.get("KEYCLOAK_ADMIN", "admin")
KC_ADMIN_PASSWORD = os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "")

# MFA 대상 Realm (M2M service-realm 제외)
MFA_REALMS = ["internal-realm", "partner-realm"]

# TOTP OTP 정책 (NIST SP 800-63B 권장: HmacSHA1, 6자리, 30초)
OTP_POLICY = {
    "otpPolicyType": "totp",
    "otpPolicyAlgorithm": "HmacSHA1",
    "otpPolicyInitialCounter": 0,
    "otpPolicyDigits": 6,
    "otpPolicyLookAheadWindow": 1,
    "otpPolicyPeriod": 30,
}

# TOTP Required Action — defaultAction=True → 첫 로그인 시 강제 등록
TOTP_ACTION: dict = {
    "alias": "CONFIGURE_TOTP",
    "name": "Configure OTP",
    "enabled": True,
    "defaultAction": True,
    "priority": 10,
    "providerId": "CONFIGURE_TOTP",
    "config": {},
}

# WebAuthn Required Actions (선택)
WEBAUTHN_ACTIONS: list[dict] = [
    {
        "alias": "webauthn-register",
        "name": "Webauthn Register",
        "enabled": True,
        "defaultAction": False,
        "priority": 70,
        "providerId": "webauthn-register",
        "config": {},
    },
    {
        "alias": "webauthn-register-passwordless",
        "name": "Webauthn Register Passwordless",
        "enabled": True,
        "defaultAction": False,
        "priority": 80,
        "providerId": "webauthn-register-passwordless",
        "config": {},
    },
]


def _get_admin_token() -> str:
    resp = httpx.post(
        f"{KC_URL}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "username": KC_ADMIN_USER,
            "password": KC_ADMIN_PASSWORD,
            "grant_type": "password",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _get_required_actions(token: str, realm: str) -> dict[str, dict]:
    """Realm의 등록된 Required Action을 {alias: data} dict로 반환."""
    resp = httpx.get(
        f"{KC_URL}/admin/realms/{realm}/authentication/required-actions",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return {a["alias"]: a for a in resp.json()}


def _put_required_action(
    token: str, realm: str, action: dict, dry_run: bool
) -> str:
    alias = action["alias"]
    if dry_run:
        status = "enabled" if action["enabled"] else "disabled"
        default = "defaultAction=True" if action["defaultAction"] else ""
        return f"[DRY-RUN] {alias}: {status} {default}"
    resp = httpx.put(
        f"{KC_URL}/admin/realms/{realm}/authentication/required-actions/{alias}",
        json=action,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return (
        f"  {alias}: enabled={action['enabled']} defaultAction={action['defaultAction']}"
    )


def _update_otp_policy(token: str, realm: str, dry_run: bool) -> str:
    if dry_run:
        return "[DRY-RUN] realm OTP policy: totp/HmacSHA1/6-digit/30s"
    # Realm PUT은 전체 realm 객체를 보내야 하므로 현재 값에 병합
    realm_resp = httpx.get(
        f"{KC_URL}/admin/realms/{realm}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    realm_resp.raise_for_status()
    realm_data = realm_resp.json()
    realm_data.update(OTP_POLICY)
    resp = httpx.put(
        f"{KC_URL}/admin/realms/{realm}",
        json=realm_data,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return "OTP policy: totp/HmacSHA1/6-digit/30s PASS"


def _apply_realm(
    token: str, realm: str, enable_webauthn: bool, dry_run: bool
) -> None:
    print(f"\n  Realm: {realm}")

    existing = _get_required_actions(token, realm)

    # 1. TOTP Required Action
    if TOTP_ACTION["alias"] in existing:
        merged = {**existing[TOTP_ACTION["alias"]], **TOTP_ACTION}
        tag = "[UPDATE]" if not (existing[TOTP_ACTION["alias"]].get("enabled") and
                                  existing[TOTP_ACTION["alias"]].get("defaultAction")) else "[SKIP]"
        print(f"    {tag} {_put_required_action(token, realm, merged, dry_run)}")
    else:
        print(f"    [WARN] CONFIGURE_TOTP 미등록 — Keycloak 버전 확인 필요")

    # 2. WebAuthn (선택)
    if enable_webauthn:
        for wa in WEBAUTHN_ACTIONS:
            if wa["alias"] in existing:
                merged = {**existing[wa["alias"]], **wa}
                tag = "[UPDATE]" if not existing[wa["alias"]].get("enabled") else "[SKIP]"
                print(f"    {tag} {_put_required_action(token, realm, merged, dry_run)}")
            else:
                print(f"    [SKIP] {wa['alias']} 미등록")

    # 3. OTP 정책
    result = _update_otp_policy(token, realm, dry_run)
    print(f"    [UPDATE] {result}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Keycloak MFA Setup — E01 T01-4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 예정 작업 출력")
    parser.add_argument("--realm", help="단일 Realm 지정")
    parser.add_argument(
        "--enable-webauthn",
        action="store_true",
        default=False,
        help="WebAuthn Required Action 활성화",
    )
    args = parser.parse_args()

    if not KC_ADMIN_PASSWORD:
        print("오류: KEYCLOAK_ADMIN_PASSWORD 환경변수 미설정", file=sys.stderr)
        sys.exit(1)

    mode = "DRY-RUN" if args.dry_run else "APPLY"
    print(f"Keycloak MFA Setup [{mode}]")
    print(f"  URL      : {KC_URL}")
    print(f"  Admin    : {KC_ADMIN_USER}")
    print(f"  WebAuthn : {'활성화' if args.enable_webauthn else '비활성화 (--enable-webauthn 으로 추가)'}")

    token = _get_admin_token()

    realms = [args.realm] if args.realm else MFA_REALMS
    for realm in realms:
        _apply_realm(token, realm, args.enable_webauthn, args.dry_run)

    print("\n완료.")


if __name__ == "__main__":
    main()
