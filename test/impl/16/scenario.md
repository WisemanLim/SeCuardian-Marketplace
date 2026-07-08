# 시험 시나리오 — impl/16: F-MP GPG 서명 검증 + mTLS (§7.3 엔터프라이즈 옵션)

- 날짜: 2026-07-08
- 대상: §9.5 잔여 "GPG 서명·mTLS". 원격 install 서명 강제 + 사설 CA/클라이언트 인증서.
- 실행: `PYTHONPATH=. python test/impl/16/test_gpg_mtls.py` (실 GPG 키쌍 생성·서명·검증)

## 범위
- `app/services/signature.py` — `verify_detached(data, sig, pubkey)` python-gnupg 임시 GNUPGHOME 격리 detached 검증, `load_pubkey(path)`.
- config: `marketplace_tls_client_cert/key`, `marketplace_gpg_pubkey_path` 추가.
- `router_marketplace_remote`:
  - `_tls_kwargs()` — CA 번들(verify) + mTLS 클라이언트 인증서(cert) httpx 옵션. `_remote_get/download` 적용.
  - install: `marketplace_install_require_signature` 시 `.sig` 다운로드→공개키 검증(실패 422, 이전 501 스텁 대체).

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | 유효 detached 서명 | True |
| 2 | 다른 데이터 서명 | False |
| 3 | 변조 데이터 | False |
| 4 | 공개키 없음 | False |
| 5 | CA 번들 | verify=경로 |
| 6 | mTLS 클라이언트 인증서 | cert=(pem,key) |
| 7 | 기본값 | verify=True, cert 없음 |
| 8 | 서명강제+유효서명 install | 201(실 배포) |
| 9 | 잘못된 서명 | 422 |
| 10 | 서명강제+공개키 미설정 | 422 |

## 판정 기준
- 10개 assert 전부 PASS. gpg 바이너리 필요(homebrew gpg 확인됨).
