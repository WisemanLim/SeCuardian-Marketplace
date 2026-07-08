"""impl/22 시험 — 화면 정렬 표준(.page) 적용 검증(PRD §7.11 impl/24).

정적 검사(소스 grep) — 전 콘텐츠 화면 루트가 `.page` 를 쓰고 `mx-auto`(가운데정렬)를 제거했는지,
전체높이 인터랙티브 레이아웃(채팅/셸)은 예외로 유지되는지 확인.

실행: PYTHONPATH=. python test/impl/22/test_alignment.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "front" / "src"
_p = _f = 0


def check(name, cond, extra=""):
    global _p, _f
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {extra}" if extra else ""))
    _p += cond
    _f += not cond


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# 1. index.css 에 .page 표준 정의
css = read(FRONT / "index.css")
check("1. index.css .page 표준 정의", re.search(r"\.page\s*\{[^}]*@apply[^}]*max-w-6xl", css) is not None)

# 2. 콘텐츠 화면 루트가 .page 사용 + mx-auto 미사용
PAGES = {
    "pages/dashboard/DashboardPage.tsx": True,
    "pages/workflow/WorkflowPage.tsx": True,
    "pages/rag/RagPage.tsx": True,
    "pages/playground/PlaygroundPage.tsx": True,
    "pages/guardrails/GuardrailsPage.tsx": True,
    "pages/agents/AgentsPage.tsx": True,  # 마켓플레이스 통합 허브
}
for rel in PAGES:
    src = read(FRONT / rel)
    has_page = 'className="page' in src
    # 페이지 루트 가운데정렬 잔존 여부(모달의 mx-4 등은 허용 — max-w-*xl mx-auto 패턴만 금지)
    centered = re.search(r"max-w-\dxl mx-auto", src) is not None
    check(f"2.{rel.split('/')[-1]} .page 사용·가운데정렬 제거", has_page and not centered,
          f"page={has_page} centered={centered}")

# 3. AI 어시스턴트(ChatPage) 는 예외 — 현행 유지(.page 미적용, 전체높이 유지)
chat = read(FRONT / "pages/ChatPage.tsx")
check("3. ChatPage 예외(현행 유지)", 'className="page' not in chat and "flex h-full" in chat)

# 4. 빌드 산출 CSS 에 .page 방출
dist = list((FRONT.parent / "dist" / "assets").glob("*.css"))
built = read(dist[0]) if dist else ""
check("4. 빌드 CSS 에 .page 방출", ".page{" in built, f"dist css={len(dist)}")

# 5. addon front — 콘텐츠 화면은 .page, 전체높이 셸은 예외
addon = ROOT / "addon-agents"
board = read(addon / "_templates/Board/Board-front.tsx")
umgr = read(addon / "_templates/UserManager/UserManager-front.tsx")
shell = read(addon / "zip/emb_server-shell/emb_server-shell-front.tsx")
check("5a. Board/UserManager .page 적용", 'className="page' in board and 'className="page' in umgr)
check("5b. 셸(emb_server-shell) 예외(h-full 유지)", "flex flex-col h-full" in shell and 'className="page' not in shell)

print(f"\n결과: {_p} PASS / {_f} FAIL")
sys.exit(1 if _f else 0)
