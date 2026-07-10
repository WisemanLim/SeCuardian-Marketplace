# wise-multi-ai-agent-template — python-fastapi (wise-dev-standard / python-fastapi)
# 참조 구현: SmartHaccp-MultiAgent
.PHONY: dev dev-be dev-fe test build deploy up down standalone docker-standalone docker-standalone-save \
        local-all local-stop local-logs local-status \
        dev-all dev-stop dev-logs \
        staging-all staging-stop staging-logs \
        prod-all prod-stop prod-logs \
        db-reset seed seed-security seed-assets db-fresh guardrails-data
ENV ?= local

# web(front) 이미지에서 배포된 ADDON 화면(front) 제외 여부 (front/Dockerfile 빌드 인자).
# api 이미지의 addon-agents/deployed 제외는 .dockerignore 가 담당(항상 제외).
# 이미지 빌드 컨테이너 환경(dev/staging/prod)은 기본 true → 배포 화면을 번들에 굽지 않음.
# ADDON 업로드 후 _rebuild_web 재빌드 시에는 이 값이 비어 false 로 처리되어 화면이 포함된다.
# 필요 시 override: SKIP_DEPLOYED_ADDONS=false make build ENV=prod
SKIP_DEPLOYED_ADDONS ?= $(if $(filter dev staging prod,$(ENV)),true,false)

# 포트를 .env.* 에서 읽는 헬퍼 (Makefile 변수, 레시피 외부에서 평가됨)
_port = $(shell grep '^$(1)=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" | xargs)

# ── 인프라 단독 (하위 호환) ───────────────────────────────────────────────────
up:      ## 인프라만 기동 (postgres + redis + ollama)
	@bash scripts/ollama_preflight.sh .env.$(ENV)
	@if docker compose --env-file .env.$(ENV) ps --status running -q ollama 2>/dev/null | grep -q .; then \
		docker compose --env-file .env.$(ENV) up -d; \
	else \
		docker compose --env-file .env.$(ENV) up -d postgres redis; \
	fi

down:    ## 전체 컨테이너 정리
	docker compose --env-file .env.$(ENV) --profile app --profile web down --remove-orphans

# ── 개발 서버 직접 실행 (터미널 분리용) ──────────────────────────────────────
dev-be:  ## 백엔드만 직접 실행 (uv + uvicorn --reload)
	@BACKEND_PORT=$$(grep '^BACKEND_PORT=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo 8100); \
	uv run uvicorn app.main:app --reload --port $${BACKEND_PORT:-8100}

dev-fe:  ## 프론트엔드만 실행 (pnpm dev)
	@FRONTEND_PORT=$$(grep '^FRONTEND_PORT=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo 4100); \
	cd front && pnpm dev --port $${FRONTEND_PORT:-4100}

dev:     ## 전체 개발환경 안내 (infra 기동 후 터미널 안내)
	@bash scripts/ollama_preflight.sh .env.$(ENV)
	@if docker compose --env-file .env.$(ENV) ps --status running -q ollama 2>/dev/null | grep -q .; then \
		docker compose --env-file .env.$(ENV) up -d; \
	else \
		docker compose --env-file .env.$(ENV) up -d postgres redis; \
	fi
	@BACKEND_PORT=$$(grep '^BACKEND_PORT=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo 8100); \
	FRONTEND_PORT=$$(grep '^FRONTEND_PORT=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo 4100); \
	echo "▶ Backend  → http://localhost:$${BACKEND_PORT:-8100}  (make dev-be)"; \
	echo "▶ Frontend → http://localhost:$${FRONTEND_PORT:-4100}  (make dev-fe)"; \
	echo "또는: make local-all  (pm2 백그라운드 통합 실행)"

# ── local — SQLite + Ollama(Docker) + BE/FE (pm2 비Docker) ───────────────────
local-all: ## local 전체 기동: Ollama Docker + BE/FE pm2 (SQLite 자동)
	@command -v pm2 >/dev/null 2>&1 || (echo "❌ pm2 필요: npm i -g pm2" && exit 1)
	mkdir -p logs
	@bash scripts/ollama_preflight.sh .env.$(ENV)
	@pm2 delete ecosystem.config.js >/dev/null 2>&1 || true
	@BACKEND_PORT=$$(grep '^BACKEND_PORT=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo 8100); \
	FRONTEND_PORT=$$(grep '^FRONTEND_PORT=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo 4100); \
	ENV=local BACKEND_PORT=$$BACKEND_PORT FRONTEND_PORT=$$FRONTEND_PORT \
		pm2 start ecosystem.config.js --env local
	pm2 save
	@BACKEND_PORT=$$(grep '^BACKEND_PORT=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo 8100); \
	FRONTEND_PORT=$$(grep '^FRONTEND_PORT=' .env.$(ENV) 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'" || echo 4100); \
	echo "▶ Backend  → http://localhost:$${BACKEND_PORT:-8100}"; \
	echo "▶ Frontend → http://localhost:$${FRONTEND_PORT:-4100}"; \
	echo "▶ 로그: make local-logs"

local-stop: ## local 전체 중단 (pm2 + ollama)
	pm2 stop ecosystem.config.js || true
	docker compose --env-file .env.$(ENV) stop ollama

local-logs: ## local 로그 모니터링 (pm2)
	pm2 logs

local-status: ## local 프로세스 상태 (pm2)
	pm2 status

# ── dev — PostgreSQL + Redis + Ollama + BE + FE (Docker Compose) ──────────────
dev-all: ## dev 전체 기동 (.env.dev, docker compose)
	@bash scripts/ollama_preflight.sh .env.dev
	@if docker compose --env-file .env.dev ps --status running -q ollama 2>/dev/null | grep -q .; then \
		docker compose --env-file .env.dev --profile app --profile web up -d; \
	else \
		docker compose --env-file .env.dev --profile app --profile web up -d --scale ollama=0; \
	fi

dev-stop: ## dev 전체 중단
	docker compose --env-file .env.dev --profile app --profile web down

dev-logs: ## dev 로그 모니터링 (docker compose)
	docker compose --env-file .env.dev --profile app --profile web logs -f

# ── staging ───────────────────────────────────────────────────────────────────
staging-all: ## staging 전체 기동 (.env.staging, docker compose)
	@bash scripts/ollama_preflight.sh .env.staging
	@if docker compose -f docker-compose.yml --env-file .env.staging ps --status running -q ollama 2>/dev/null | grep -q .; then \
		docker compose -f docker-compose.yml --env-file .env.staging --profile app --profile web up -d; \
	else \
		docker compose -f docker-compose.yml --env-file .env.staging --profile app --profile web up -d --scale ollama=0; \
	fi

staging-stop: ## staging 전체 중단
	docker compose -f docker-compose.yml --env-file .env.staging --profile app --profile web down

staging-logs: ## staging 로그 모니터링
	docker compose -f docker-compose.yml --env-file .env.staging --profile app --profile web logs -f

# ── prod ──────────────────────────────────────────────────────────────────────
prod-all: ## prod 전체 기동 (.env.prod, docker compose)
	@bash scripts/ollama_preflight.sh .env.prod
	@if docker compose -f docker-compose.yml --env-file .env.prod ps --status running -q ollama 2>/dev/null | grep -q .; then \
		docker compose -f docker-compose.yml --env-file .env.prod --profile app --profile web up -d; \
	else \
		docker compose -f docker-compose.yml --env-file .env.prod --profile app --profile web up -d --scale ollama=0; \
	fi

prod-stop: ## prod 전체 중단
	docker compose -f docker-compose.yml --env-file .env.prod --profile app --profile web down

prod-logs: ## prod 로그 모니터링
	docker compose -f docker-compose.yml --env-file .env.prod --profile app --profile web logs -f api

# ── DB 관리 ───────────────────────────────────────────────────────────────────
# ENV=local(기본): 호스트에서 직접 실행 (SQLite)
# ENV=dev|staging|prod: 컨테이너 내 실행 (PostgreSQL)
#
# DB 초기화는 아래 db-reset / db-fresh 를 **직접 실행할 때만** 수행된다.
# make *-all / up / dev 등 기동 명령은 DB 를 초기화하지 않는다
# (앱 기동 시 seed(02_seed.sql)는 파일 해시 마커로 최초 1회만 적용 — app/db.py run_migrations).
_DB_RUN = $(if $(filter dev staging prod,$(ENV)),docker exec secuardian-api-1 uv run,uv run)

# 파괴적 명령 확인 가드 — FORCE=1 로 스킵 (CI 등)
define _CONFIRM_DESTRUCTIVE
	@if [ "$(FORCE)" != "1" ]; then \
		printf "⚠️  ENV=$(ENV) DB 데이터가 삭제됩니다. 계속하려면 'yes' 입력: "; \
		read ans; [ "$$ans" = "yes" ] || { echo "취소됨"; exit 1; }; \
	fi
endef

db-reset: ## DB 데이터 삭제 + 스키마 재생성 — 명시적 초기화 (FORCE=1 로 확인 생략)
	$(_CONFIRM_DESTRUCTIVE)
	$(_DB_RUN) python scripts/db_reset.py

seed:    ## 기본 설정 + 테스트 계정 삽입 — 기반 시드만 (ENV=prod make seed)
	$(_DB_RUN) python scripts/seed.py

seed-security: ## 보안 에이전트 13종 자산 카탈로그 등록 (§7.6.1 — seed 와 분리, 필요 시 명시 실행)
	$(_DB_RUN) python scripts/seed_security.py

seed-assets: ## marketplace-assets/{security,utilities} 스캔 자산 등록 (§7.6.2 — 미등록만 INSERT)
	$(_DB_RUN) python scripts/seed_assets.py

cleanup-addons: ## 미설치 자산 hot-deploy 잔재 + 고아 deployed 디렉터리 일괄 정리 (§7.6.5, 멱등)
	$(_DB_RUN) python scripts/cleanup_addon_remnants.py

guardrails-data: ## F-GRD 도메인 규칙 데이터 재컴파일 (GUARDRAILS_SCRIPTS_DIR 로 소스 지정, §7.8.7)
	$(_DB_RUN) python scripts/build_guardrails_data.py

db-fresh: ## db-reset + seed(기반) + seed-security + seed-assets — 초기화 직후 security·utilities 등록 상태 (§7.6.3, FORCE=1 로 확인 생략)
	$(_CONFIRM_DESTRUCTIVE)
	$(_DB_RUN) python scripts/db_reset.py
	$(_DB_RUN) python scripts/seed.py
	$(_DB_RUN) python scripts/seed_security.py
	$(_DB_RUN) python scripts/seed_assets.py

# ── CI / 품질 ─────────────────────────────────────────────────────────────────
test:    ## pytest 실행
	uv run pytest

lint:    ## ruff 검사
	uv run ruff check .

# ── 빌드 / 배포 ───────────────────────────────────────────────────────────────
build:   ## 앱 이미지 빌드 (profiles:app + web) — 기본 이미지는 배포 ADDON 제외 (dev/staging/prod)
	SKIP_DEPLOYED_ADDONS=$(SKIP_DEPLOYED_ADDONS) docker compose --env-file .env.$(ENV) --profile app --profile web build

deploy:  ## Helm 배포
	helm upgrade --install wise-multi-ai-agent-template ./deploy/helm

