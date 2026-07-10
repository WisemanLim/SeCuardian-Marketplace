"""test/impl/46 — worker 가이드 포팅 + 카탈로그 카드덱 개편 + 가드레일 카탈로그명 다국어.

정적/파일시스템 검증 — 서버 기동 불필요 (worker 메타는 실제 marketplace-assets 로 해석).
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTER = ROOT / "app/routers/router_addon_agent.py"
MODAL = ROOT / "front/src/pages/agents/WorkerGuideModal.tsx"
PAGE = ROOT / "front/src/pages/agents/AgentsPage.tsx"
MP_PAGE = ROOT / "front/src/pages/marketplace/MarketplacePage.tsx"
API = ROOT / "front/src/api/addonAgents.ts"


def test_tc_46_01_worker_endpoints():
    src = ROUTER.read_text(encoding="utf-8")
    for token in ("_agent_worker_meta", "_worker_summary",
                  '"/{agent_key}/worker-guide"', '"/{agent_key}/worker-package"',
                  'row["has_worker"]', 'result["worker"]'):
        assert token in src, token


def test_tc_46_02_worker_meta_resolution():
    import sys
    sys.path.insert(0, str(ROOT))
    import os
    cwd = os.getcwd()
    os.chdir(ROOT)  # _MARKET_ASSETS 상대경로
    try:
        from app.routers.router_addon_agent import _agent_worker_meta, _worker_summary
        w, src = _agent_worker_meta("vasca-cve")
        assert w and w["kind"] == "bundled" and w["package"] == "VASCA_worker.zip"
        assert (src / w["guide"]).exists()
        s = _worker_summary(w, "vasca-cve")
        assert s["download_path"].endswith("/worker-package")
        w2, _ = _agent_worker_meta("agentic-soc")
        assert w2 and w2["kind"] == "external" and "package" not in w2
    finally:
        os.chdir(cwd)


def test_tc_46_03_front_parity():
    modal = MODAL.read_text(encoding="utf-8")
    assert "prose prose-sm" not in modal and "components={mdComponents}" in modal
    page = PAGE.read_text(encoding="utf-8")
    assert page.count("<WorkerCorner agentKey=") == 2
    assert "<WorkerGuideModal" in page
    api = API.read_text(encoding="utf-8")
    assert "getWorkerGuide" in api and "has_worker?: boolean" in api
    for loc in ("ko", "en"):
        txt = (ROOT / f"front/src/locales/{loc}.json").read_text(encoding="utf-8")
        for key in ("workerGuideTitle", "workerRequired", "workerDownload", "workerGuideMissing"):
            assert f'"{key}"' in txt, f"{loc}:{key}"


def test_tc_46_04_05_06_catalog_cards():
    src = MP_PAGE.read_text(encoding="utf-8")
    assert "mp.catalogDesc" not in src                       # TC-46-04
    assert "CATEGORY_TONE" in src and "DEFAULT_TONE" in src  # TC-46-06
    assert "violet" in src and "emerald" in src
    # TC-46-05: 배지가 이름 행 내부, 버튼이 카드 헤더 행(우상단)
    name_block = src.index("flex items-center gap-1.5 min-w-0")
    badge = src.index("mp.installed", name_block)
    assert badge - name_block < 600, "배지는 이름 옆 행 내부"
    header = src.index("flex items-start justify-between gap-2")
    install_btn = src.index("handleInstall(a)", header)
    desc_line = src.index("assetDesc(a) && <p", header)
    assert install_btn < desc_line, "설치 버튼은 설명보다 위(카드 우상단 행)"


def test_tc_46_09_config_path_worker():
    """결함 수정(사용자 보고): 에이전트(설치됨) 탭 활성화 시 팝업 미표시 + 카드 아이콘 미표시."""
    cfg_router = (ROOT / "app/routers/router_agent_config.py").read_text(encoding="utf-8")
    assert 'result["worker"]' in cfg_router          # patch_agent 활성화 응답
    assert 'a["has_worker"]' in cfg_router           # list_agents 응답
    cfg_api = (ROOT / "front/src/api/agentConfig.ts").read_text(encoding="utf-8")
    assert "has_worker?: boolean" in cfg_api and "worker?: WorkerInfo" in cfg_api
    page = PAGE.read_text(encoding="utf-8")
    assert "configs.filter((c) => c.has_worker)" in page      # workerKeys = configs∪addons
    assert "result?.worker) setWorkerGuideKey" in page        # config 토글 팝업


def test_tc_46_07_guardrails_i18n():
    src = (ROOT / "app/services/guardrails_rules.py").read_text(encoding="utf-8")
    assert src.count("display_name_en") >= 3  # UPDATE + INSERT + name_en 추출
    grd = (ROOT / "front/src/pages/guardrails/GuardrailsPage.tsx").read_text(encoding="utf-8")
    assert "pickDescription(null, d.display_name, d.display_name_en)" in grd
    db_path = ROOT / "local.db"
    if db_path.exists():  # dev DB 직접 패치 검증 (CI 등 무DB 환경은 스킵)
        db = sqlite3.connect(db_path)
        cols = {r[1] for r in db.execute("PRAGMA table_info(guardrails_domain_catalog)")}
        assert "display_name_en" in cols
        n = db.execute(
            "SELECT count(*) FROM guardrails_domain_catalog "
            "WHERE display_name_en IS NOT NULL AND display_name_en != ''"
        ).fetchone()[0]
        assert n >= 20, f"영문 카탈로그명 채움 {n}행"
