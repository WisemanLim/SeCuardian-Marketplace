# 시험 결과 — impl/16

- 날짜: 2026-07-08
- 판정: **PASS** (10/10)

## 실행 결과
```
PASS valid detached signature -> True
PASS wrong-data signature -> False
PASS tampered data -> False
PASS no pubkey -> False
PASS CA bundle → verify path
PASS mTLS client cert pair
PASS defaults → verify True, no cert
PASS signed install (valid sig) -> 201
PASS bad signature -> 422
PASS no pubkey configured -> 422
=== RESULT: ALL PASS
```

## 검증 항목
- 실 GPG 키쌍(RSA2048, no_protection)으로 detached 서명 생성→검증 — python-gnupg 임시 GNUPGHOME 격리(시스템 keyring 미오염).
- 원격 install 서명 강제(`MARKETPLACE_INSTALL_REQUIRE_SIGNATURE=true`): `.sig` 다운로드→공개키 검증, 실패/미구성 422(이전 501 스텁 대체).
- mTLS: CA 번들(`verify=경로`) + 클라이언트 인증서(`cert=(pem,key)`) httpx 옵션 조립. 미설정 시 기본 verify=True.
- `ruff check` 0오류. 테스트 배포 산출물 정리.

## 미결/후속
- 서명 강제 운영 절차(공개키 배포·로테이션)는 문서화 대상. 실 mTLS 핸드셰이크는 사설 CA 인프라 환경에서 검증.
