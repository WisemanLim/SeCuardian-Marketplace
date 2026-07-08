"""GPG 서명 검증 (F-MP §7.3 엔터프라이즈 옵션).

원격 자산 ZIP 의 detached 서명(`.sig`)을 배포자의 공개키로 검증한다. python-gnupg 사용,
격리된 임시 GNUPGHOME 에 공개키를 임포트해 부작용 없이 검증한다(시스템 keyring 미오염).
"""
import logging
import tempfile

logger = logging.getLogger("uvicorn.error")


def verify_detached(data: bytes, signature: bytes, pubkey_armored: str) -> bool:
    """detached 서명 검증. 공개키·서명·데이터가 일치하고 유효하면 True.

    실패/오류/미구성 시 False (호출측이 422 로 처리). 검증은 임시 GNUPGHOME 격리.
    """
    if not pubkey_armored or not signature:
        return False
    try:
        import gnupg
    except Exception:  # noqa: BLE001 — 라이브러리 미설치 시 검증 불가
        logger.warning("[signature] python-gnupg 미설치 — 서명 검증 불가")
        return False
    with tempfile.TemporaryDirectory() as home:
        try:
            gpg = gnupg.GPG(gnupghome=home)
            imported = gpg.import_keys(pubkey_armored)
            if not imported.count:
                logger.warning("[signature] 공개키 임포트 실패")
                return False
            with tempfile.NamedTemporaryFile(suffix=".sig") as sigf:
                sigf.write(signature)
                sigf.flush()
                verified = gpg.verify_data(sigf.name, data)
            return bool(verified.valid)
        except Exception:  # noqa: BLE001
            logger.exception("[signature] 검증 오류")
            return False


def load_pubkey(path: str) -> str:
    """공개키 파일(armored) 읽기. 없으면 빈 문자열."""
    if not path:
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:  # noqa: BLE001
        logger.warning("[signature] 공개키 파일 읽기 실패: %s", path)
        return ""
