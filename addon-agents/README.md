# Addon Agent 가이드

> **SeCuardian**의 확장 모듈 시스템입니다.  
> 관리자가 커스텀 Agent(게시판, 설문, 재고 등)를 zip 파일로 만들어 업로드하면, 앱을 재시작하지 않고 즉시 API·DB가 배포(핫 디플로이)됩니다.  
> 프론트엔드 컴포넌트(`-front.tsx`)가 포함된 경우, 프론트엔드 재빌드 후 사이드바 메뉴에 자동으로 표시됩니다.

---

## Agent 만들기 방법

두 가지 방법 중 선택할 수 있습니다.

| 방법 | 설명 | 진입 |
|------|------|------|
| **스캐폴딩 Wizard** | 9종 유형 중 선택 → 이름/설명/도메인 입력 → ZIP 자동 생성 | 에이전트 관리 → 새 Agent 만들기 → **스캐폴딩 만들기** 탭 |
| **ZIP 업로드** | 직접 개발한 ZIP 파일 업로드 | 에이전트 관리 → 새 Agent 만들기 → **ZIP 업로드 등록** 탭 |

스캐폴딩 Wizard는 서버 API `/api/addon-agents/scaffold`를 통해 ZIP을 생성하며, "바로 배포" 버튼으로 즉시 등록도 가능합니다.

---

## 디렉터리 구조

```
addon-agents/
├── _templates/              개발용 템플릿 (완성본 zip 포함)
│   ├── Board/               App Agent — 게시판 + 댓글
│   │   ├── Board-app.py
│   │   ├── Board-front.tsx
│   │   ├── Board-sql.sql
│   │   └── Board-meta.json
│   ├── RagAgent/            RAG Agent — 문서 임베딩 + 벡터 검색 Q&A
│   │   ├── RagAgent-app.py
│   │   ├── RagAgent-sql.sql
│   │   └── RagAgent-meta.json
│   ├── ServiceAgent/        Service Agent — 백엔드 비즈니스 로직
│   │   ├── ServiceAgent-app.py
│   │   └── ServiceAgent-meta.json
│   ├── ToolProxyAgent/      Tool Proxy Agent — 외부 API → MCP 어댑터
│   │   ├── ToolProxyAgent-app.py
│   │   └── ToolProxyAgent-meta.json
│   ├── ShellAgent/          Shell Agent — 서버 상태 점검 CLI/셸 터미널 (읽기 전용)
│   │   ├── ShellAgent-app.py
│   │   ├── ShellAgent-front.tsx
│   │   └── ShellAgent-meta.json
│   ├── Board.zip            ↗ 등록 가능한 완성 패키지
│   ├── RagAgent.zip
│   ├── ServiceAgent.zip
│   ├── ToolProxyAgent.zip
│   └── ShellAgent.zip
└── deployed/                업로드 후 자동 생성 (내장 에이전트 제외: 직접 편집 금지)
    └── {agent_key}/
        ├── {AgentName}-app.py
        ├── {AgentName}-front.tsx   (선택)
        ├── {AgentName}-sql.sql     (선택)
        └── {AgentName}-meta.json
```

> **내장 에이전트** (`deployed/board/`)는 git에 포함되어 있으며 앱 시작 시 자동 로드됩니다.

---

## 파일 명명 규칙

| 구성 요소 | 파일명 패턴 | 역할 |
|-----------|-------------|------|
| 메타데이터 | `{AgentName}-meta.json` | Agent 유형·capability·거버넌스 정의 (권장) |
| API 라우터 | `{AgentName}-app.py` | FastAPI `router` 객체 export (선택) |
| 프론트 컴포넌트 | `{AgentName}-front.tsx` | React 컴포넌트 — 독립형 i18n·다크모드 (선택) |
| DB 스키마 | `{AgentName}-sql.sql` | 테이블 생성 DDL, 자동 적용 (선택) |
| 완성 패키지 | `{AgentName}.zip` | 위 파일들을 루트에 flat zip |

> **AgentName**: PascalCase 권장 (예: `Board`, `SurveyForm`, `Inventory`)  
> `-app.py` 또는 `-front.tsx` 중 최소 하나 필요합니다.  
> zip 내부는 서브디렉터리 없이 파일만 포함해야 합니다.

### emb_ prefix — 내장 유래 에이전트 명명 규약

- **`emb_` prefix** = 플랫폼 내장(embedded) 에이전트의 ADDON 판 표식 (예: `emb_vasca-cve`, `emb_cilium-netpol`).
  순수 ADDON(내장 tbl_agent_config 목록에 없는 에이전트, 예: `caddy-proxy`·`grafana-dashboard`·`truffle-scan`)
  은 prefix 없이 명명하여 서로 구별합니다.
- **내장 에이전트 자체의 key 와 에이전트 관리 '내장 에이전트' 탭 표출 이름에는 emb_ 를 붙이지 않습니다** —
  emb_ 는 ADDON 패키징(zip·addon key)에만 적용됩니다.
- 내장 에이전트를 ADDON 화하거나 추가 구현할 때는 **반드시 `emb_` prefix** 를 사용하고
  `addon-agents/zip/emb_{key}/` 에 소스, `addon-agents/zip/emb_{key}.zip` 으로 패키징합니다.
- meta.json 의 `key`(또는 `agent_key`) 필드도 `emb_` prefix 를 포함해야 하며,
  `base_agent` 필드에 원본 내장 라우터 출처를 기록합니다.
- ⚠️ addon `-app.py` 에서 `from __future__ import annotations` 는 사용 금지 —
  동적 로더(`spec_from_file_location`)가 모듈을 `sys.modules` 에 등록하지 않아
  pydantic 이 지연 어노테이션(request body 모델)을 해석하지 못해 500 오류가 발생합니다.

### 화면 정렬 표준 (`-front.tsx`, PRD §7.11 impl/24)

- 에이전트 화면(`-front.tsx`)의 **최상위 컨테이너에 `.page` 클래스**를 적용한다
  (`front/src/index.css` 정의 = `w-full max-w-6xl p-4 sm:p-6`). **좌측정렬·반응형·최대폭 제한**으로 전 화면을 통일.
- `mx-auto`(가운데 정렬) 금지, `max-w-4xl/5xl` 등 개별 폭 지정 금지 — `.page` 로 표준화.
- 예: `<div className="page space-y-4"> … </div>` (그리드면 `page grid grid-cols-3 gap-4`).
- **예외**: 채팅·터미널 등 **전체높이 인터랙티브 레이아웃**(`flex flex-col h-full`)은 `.page` 미적용
  (AI 어시스턴트·ShellAgent·emb_server-shell 등). 그 외 콘텐츠·폼 화면은 모두 `.page` 준용.

---

## Agent 개발 절차 (Makefile 사용)

`addon-agents/` 디렉터리의 **Makefile**로 초기화·검증·패키징을 자동화합니다.

```bash
# addon-agents/ 디렉터리에서 실행
cd addon-agents/

make init    AGENT=Survey   # 템플릿 스캐폴딩
make test    AGENT=Survey   # 구조·문법 검증
make publish AGENT=Survey   # zip 패키징
make clean   AGENT=Survey   # 생성 파일 삭제
```

| 타겟 | 설명 |
|------|------|
| `make init AGENT=<name>` | Board 템플릿 복사 + `Board` → `<name>` 치환 → `_templates/<name>/` 생성 |
| `make test AGENT=<name>` | 파일 존재·Python 문법·router export·SQL 구조·React export 검증 |
| `make publish AGENT=<name>` | `_templates/<name>.zip` 생성 (업로드 준비) |
| `make clean AGENT=<name>` | 생성된 디렉터리 및 zip 삭제 |

---

## 파일 작성 가이드

### `{AgentName}-sql.sql`

- SQLite/PostgreSQL 공통 문법 권장 (`NOT is_deleted`, `CURRENT_TIMESTAMP`)
- 테이블명 접두사 `tbl_` 권장
- 모든 DDL에 `CREATE TABLE IF NOT EXISTS` 사용

```sql
CREATE TABLE IF NOT EXISTS tbl_myfeature (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    is_deleted  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

> PostgreSQL 전용 문법(`SERIAL`, `BOOLEAN`, `NOW()`)은 업로드 시 자동 변환됩니다.

### `{AgentName}-app.py`

**필수 규칙:**
- `router` 변수명으로 `APIRouter` 인스턴스 export
- Wise 앱 모듈 사용: `from app.core.deps import get_current_user`, `from app.db import fetch_all, fetch_one, execute_write, execute_insert, _PH`
- 마운트 최종 경로: `/api/addon/{agent_key}/{prefix}/...`

```python
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.db import _PH, execute_insert, fetch_all

router = APIRouter(prefix="/items", tags=["myfeature"])

@router.get("")
async def list_items(user: dict = Depends(get_current_user)):
    return {"items": await fetch_all("SELECT * FROM tbl_myfeature WHERE NOT is_deleted")}
```

### `{AgentName}-front.tsx`

- API 호출 경로: `/api/addon/{agent_key}/{prefix}/...`
- `import client from "../../../api/client"` 사용 (Wise axios 인스턴스)
- **독립형 i18n**: `localStorage.getItem("locale")` + `localeChanged` 이벤트 구독
- **다크모드**: Tailwind `dark:` 클래스 (앱 테마와 자동 동기화)
- **내부 페이지 타이틀 금지**: 상단 헤더(AppLayout)가 에이전트명을 자동 표시하므로,
  컴포넌트 본문 최상단에 에이전트명 `<h1>` 을 넣지 않는다. 대신 **페이지 설명 한 줄**을
  `<p className="text-sm text-gray-500 dark:text-gray-400">` 로 표시한다.
  (하위 뷰 제목 — 예: '새 글 작성' 폼 헤딩 — 은 허용)

```tsx
const LOCALE = {
  ko: { desc: "내 기능을 관리합니다." },
  en: { desc: "Manage my feature." },
};

function useLocale() {
  const [locale, setLocale] = useState(() => localStorage.getItem("locale") || "ko");
  useEffect(() => {
    const h = () => setLocale(localStorage.getItem("locale") || "ko");
    window.addEventListener("localeChanged", h);
    return () => window.removeEventListener("localeChanged", h);
  }, []);
  return (k: string) => LOCALE[locale]?.[k] ?? LOCALE.ko[k] ?? k;
}

export default function MyFeaturePage() {
  const t = useLocale();
  // 타이틀은 상단 헤더가 에이전트명으로 표시 — 본문에는 설명만
  return <p className="text-sm text-gray-500 dark:text-gray-400">{t("desc")}</p>;
}
```

### `{AgentName}-meta.json`

Orchestrator의 capability-based routing과 거버넌스 게이트에서 사용됩니다.

> **설명 다국어(i18n)**: `description`(한국어) + `description_en`(영어) 두 필드를 모두 작성한다.
> UI '언어' 선택이 en 이면 `description_en` 을, ko 이면 `description` 을 표시한다
> (`description_en` 누락 시 `description` 폴백). 에이전트 관리 카드·툴팁, 화면 없는
> addon 의 Q&A 폴백 헤더에 적용된다.

**agent_type 지원 목록:**

| agent_type | 용도 |
|------------|------|
| `app` | UI + CRUD 앱 (게시판, 설문 등) |
| `service` | 백엔드 비즈니스 로직 |
| `rag` | 문서 임베딩 + 벡터 검색 Q&A |
| `tool-proxy` | 외부 REST API → MCP 어댑터 |
| `reviewer` | 응답 품질·위험도 리뷰 게이트 |
| `execution` | 코드·명령 실행 Agent |
| `hitl` | Human-in-the-Loop 승인 게이트 |
| `memory` | 장기 메모리·컨텍스트 저장 |
| `federation` | 다른 Agent 시스템 연결 |

**전체 스키마:**

```json
{
  "agent_type": "service",
  "version": "1.0.0",
  "display_name": "내 Agent",
  "description": "Agent 설명 (한국어 — UI 언어 ko 에서 표시)",
  "description_en": "Agent description (English — shown when UI language is en; falls back to description)",
  "capabilities": [
    {
      "verb": "process",
      "domain": "service.myfeature",
      "description": "기능 설명",
      "input_schema": {
        "type": "object",
        "properties": { "input": { "type": "object" } },
        "required": ["input"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "output": { "type": "object" },
          "status": { "type": "string" }
        }
      },
      "qos": {
        "max_latency_ms": 10000,
        "supports_async": true,
        "supports_streaming": true
      }
    }
  ],
  "governance": {
    "data_classification": "internal",
    "human_approval_required": false,
    "audit_level": "standard"
  },
  "required_env": [],
  "optional_env": ["ANTHROPIC_API_KEY"],
  "min_platform_version": "2.0.0"
}
```

| 필드 | 설명 |
|------|------|
| `capabilities[].verb` | Orchestrator가 intent 라우팅에 사용 (`retrieve`, `process`, `proxy`, `manage` 등) |
| `capabilities[].domain` | `{category}.{subdomain}` 형식 |
| `governance.human_approval_required` | `true` 시 HITL 게이트 강제 |
| `required_env` | 미설정 시 배포 경고 (예: `TOOL_PROXY_BASE_URL`) |
| `optional_env` | 기능 향상 선택 환경변수 (예: `ANTHROPIC_API_KEY`) |
| `min_platform_version` | 하위 플랫폼 버전 호환성 체크 |

---

## zip 패키징 및 업로드

```bash
# Makefile 사용 (권장)
make publish AGENT=MyFeature
# → _templates/MyFeature.zip 생성

# 수동
zip -j _templates/MyFeature.zip \
    _templates/MyFeature/MyFeature-app.py \
    _templates/MyFeature/MyFeature-front.tsx \
    _templates/MyFeature/MyFeature-sql.sql
```

### 업로드 절차

1. **에이전트 관리** 페이지 → **새 Agent 만들기** 버튼 → **ZIP 업로드 등록** 탭
2. zip 파일 선택 (또는 제공된 템플릿 zip 다운로드 후 업로드)
3. 자동 처리:
   - `-sql.sql` 실행 → DB 테이블 생성
   - `-app.py` 동적 로드 → API 즉시 활성화
   - `-front.tsx` → `front/src/pages/addon/deployed/{key}.tsx` 복사
   - `tbl_addon_agents` + `tbl_agent_config` 등록
4. **프론트엔드 재빌드** → 사이드바 메뉴 자동 표시:
   ```bash
   cd front && npm run build
   pm2 restart wise-fe
   ```

---

## 핫 디플로이 메커니즘

```
zip 업로드
    │
    ▼
addon-agents/deployed/{agent_key}/ 에 파일 저장
    │
    ├─ {Name}-sql.sql 실행 → DB 테이블 생성
    │
    ├─ {Name}-app.py  importlib 동적 로드
    │   → module.router 추출
    │   → app.include_router(router, prefix="/api/addon/{agent_key}")
    │
    ├─ {Name}-front.tsx → front/src/pages/addon/deployed/{key}.tsx 복사
    │   → 프론트엔드 재빌드 후 /addon/{key} 라우트 자동 활성화
    │
    └─ tbl_addon_agents + tbl_agent_config INSERT

앱 재시작 시: addon_agent_loader._load_all_from_disk()
→ DB 활성 Addon 조회 → 모든 라우터 자동 재등록
```

---

## API 엔드포인트

| Method | 경로 | 설명 | 권한 |
|--------|------|------|------|
| `GET` | `/api/addon-agents/` | 등록된 Addon 목록 | 로그인 |
| `POST` | `/api/addon-agents/upload` | zip 업로드 + 핫 디플로이 | supervisor/admin |
| `POST` | `/api/addon-agents/scaffold` | 스캐폴딩 Wizard → zip 생성 (또는 바로 배포) | supervisor/admin |
| `PATCH` | `/api/addon-agents/{key}/toggle` | 활성/비활성 토글 | supervisor/admin |
| `DELETE` | `/api/addon-agents/{key}` | Agent 삭제 | supervisor/admin |
| `GET` | `/api/addon-agents/templates/list` | 템플릿 목록 | 로그인 |
| `GET` | `/api/addon-agents/templates/download/{file}` | 템플릿 zip 다운로드 | 로그인 |

---

## 제약 및 주의사항

| 항목 | 내용 |
|------|------|
| 보안 | 업로드된 Python 파일은 서버에서 실행됨 — supervisor/admin 권한 보호 필수 |
| 라우터 제거 | Agent 삭제 후 라우터 완전 제거는 **앱 재시작** 필요 |
| 프론트 반영 | `-front.tsx` 포함 시 `npm run build` + 서버 재시작 필요 |
| 파일 크기 | zip 최대 10MB |
| 내장 에이전트 | `deployed/board/` 은 직접 수정 가능 (git 추적됨) |

---

## 내장 에이전트

| Agent | 설명 | 경로 |
|-------|------|------|
| **Board** | 게시판 (글쓰기·수정·삭제, 댓글 작성·삭제, 페이지네이션) | `/addon/board` |

### 내장 에이전트 ADDON 판 (`zip/emb_*`) + 순수 ADDON

플랫폼 내장 에이전트(tbl_agent_config 시드)의 ADDON 패키징은 `emb_` prefix, 내장 목록에 없는
순수 ADDON 은 prefix 없이 관리합니다. `addon-agents/zip/{key}.zip` 을 에이전트 관리에서
업로드하면 `/api/addon/{key}` 로 배포됩니다.

**내장 유래 (`emb_`) 13종:**

| # | ADDON key | 원본 내장 | 비고 |
|---|-----------|----------|------|
| 1 | `emb_agentic-soc` | agentic-soc | Agentic SOC 오케스트레이션 |
| 2 | `emb_ai-eval-gate` | ai-eval-gate (router_ai_eval) | **신규 포팅** — PyRIT/SkillSpector 게이트 |
| 3 | `emb_ai-redteam` | ai-redteam | ⚠️ isolated |
| 4 | `emb_behavior-noti` | behavior-noti | C++ 행위 알림 |
| 5 | `emb_cilium-netpol` | cilium-netpol | eBPF 네트워크 정책 |
| 6 | `emb_isms-p-evidence` | isms-p-evidence (router_isms) | **신규 포팅** — ISMS-P 증거 수집 |
| 7 | `emb_neosync-dlp` | neosync-dlp | DLP 파이프라인 |
| 8 | `emb_otel-collector` | otel-collector | OTel 관측성 |
| 9 | `emb_shuffle-soar` | shuffle-soar | SOAR 워크플로 |
| 10 | `emb_teleport-pam` | teleport-pam | PAM 감사 |
| 11 | `emb_teler-ids` | teler-ids | HTTP IDS |
| 12 | `emb_vasca-cve` | vasca-cve (router_vasca) | **신규 포팅** — CVE 스캔 |
| 13 | `emb_velociraptor-dfir` | velociraptor-dfir | DFIR 수집 |

**순수 ADDON (prefix 없음) 4종:** `caddy-proxy`(리버스 프록시 모니터) · `grafana-dashboard`(대시보드 RAG + sql) · `truffle-scan`(시크릿 스캔 수신) · `ai-traffic-monitor`(브라우저 AI 도우미 트래픽 사용량 모니터 — vnstat/nethogs/tcpdump/tshark 래핑)

> `general`(Orchestrator)·`chat`(AI 어시스턴트) 은 required 코어로 ADDON 화 대상에서 제외.
> 신규 포팅 3종은 내장판(settings 기반)과 달리 **환경변수 기반 설정**이며 인메모리 저장소는 내장판과 독립입니다.

---

## 템플릿 목록

| 템플릿 | agent_type | 설명 | 파일 |
|--------|------------|------|------|
| **Board** | `app` | 댓글 포함 게시판 — 글쓰기·수정·삭제·페이지네이션, React UI 포함 | `Board.zip` |
| **RagAgent** | `rag` | 문서 임베딩·청킹·벡터 검색 + SSE 스트리밍 Q&A. 임베딩 함수 교체 포인트 포함 | `RagAgent.zip` |
| **ServiceAgent** | `service` | 백엔드 비즈니스 로직 뼈대. `process` capability, async/streaming 지원 | `ServiceAgent.zip` |
| **ToolProxyAgent** | `tool-proxy` | 외부 REST API를 MCP Tool로 노출하는 어댑터. `TOOL_PROXY_BASE_URL` 필수 | `ToolProxyAgent.zip` |

### RagAgent 주요 엔드포인트

| Method | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/addon/ragagent/ingest` | 문서 업로드 + 청킹 + 임베딩 저장 |
| `GET` | `/api/addon/ragagent/documents` | 업로드된 문서 목록 |
| `DELETE` | `/api/addon/ragagent/documents/{id}` | 문서 + 청크 삭제 (supervisor/admin) |
| `POST` | `/api/addon/ragagent/search` | 코사인 유사도 벡터 검색 |
| `POST` | `/api/addon/ragagent/qa` | RAG 기반 Q&A — SSE 스트리밍 응답 |

> `_embed()` 함수는 프로토타입 구현(해시 기반)입니다. 실제 서비스에서는 Ollama `nomic-embed-text` 또는 OpenAI `text-embedding-3-small`로 교체하세요.

---

_SeCuardian · Addon Agent Extension System_
