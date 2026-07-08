# 시험 시나리오 — impl/22: 화면 정렬 표준화(.page)

- 날짜: 2026-07-09
- 대상(PRD §7.11 impl/24, 변경이력 v0.19)
- 실행: `PYTHONPATH=. uv run python test/impl/22/test_alignment.py` (정적 소스 검사)

## 범위
- `front/src/index.css` 에 **`.page` 표준 클래스**(`w-full max-w-6xl p-4 sm:p-6`) 정의.
- 콘텐츠 화면(대시보드·워크플로우·RAG·플레이그라운드·가드레일·마켓플레이스 허브) 루트를 `.page` 로 통일,
  `max-w-4xl/5xl mx-auto`(가운데정렬) 제거 → **좌측정렬·반응형**.
- addon front(Board·UserManager 템플릿) 동일 적용.
- **예외**: 전체높이 인터랙티브 레이아웃 — AI 어시스턴트(ChatPage), ShellAgent/emb_server-shell(셸) 현행 유지.

## 시험 케이스
| # | 케이스 | 기대 |
|---|---|---|
| 1 | .page 표준 정의 | index.css 에 존재 |
| 2 | 6개 화면 루트 | .page 사용 + 가운데정렬 제거 |
| 3 | ChatPage 예외 | .page 미적용·전체높이 유지 |
| 4 | 빌드 CSS | `.page{` 방출 |
| 5a | addon Board/UserManager | .page 적용 |
| 5b | addon 셸 | 예외(h-full) 유지 |

## 판정 기준
- test_alignment.py 11/11 PASS + 프론트 tsc/build 0오류 = PASS.
