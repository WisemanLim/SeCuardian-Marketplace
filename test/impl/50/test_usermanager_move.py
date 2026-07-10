"""impl/50 — UserManager utilities → addon 이관 + 시드 고아 정리 (격리 sqlite, subprocess seed)."""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
tmp = tempfile.mkdtemp()
DB = f"{tmp}/t.db"
ENV = {**os.environ, "ENV": "local", "DATABASE_URL": f"sqlite:///{DB}",
       "JWT_SECRET_KEY": "test-secret-key-32-characters-min-xx",
       "OLLAMA_WARMUP_ENABLED": "false", "AGENT_STANDALONE": "1"}

fails = []


def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)


def run_seed() -> str:
    r = subprocess.run([sys.executable, "scripts/seed_assets.py"],
                       cwd=ROOT, env=ENV, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(r.stdout[-1500:], r.stderr[-1500:])
    chk(r.returncode == 0, "seed_assets 실행 성공")
    return r.stdout


# TC-50-01: 디렉터리 배치
chk((ROOT / "marketplace-assets/addon/UserManager").is_dir(), "TC-50-01 addon/UserManager 디렉터리")
chk((ROOT / "marketplace-assets/addon/UserManager.zip").exists(), "TC-50-01 addon/UserManager.zip")
chk(not (ROOT / "marketplace-assets/utilities/UserManager").exists(), "TC-50-01 utilities 디렉터리 부재")
chk(not (ROOT / "marketplace-assets/utilities/UserManager.zip").exists(), "TC-50-01 utilities zip 부재")

# TC-50-02: 격리 DB 시드 — usermanager 미시드, utilities 5종
run_seed()
con = sqlite3.connect(DB)
rows = dict(con.execute("SELECT asset_key, category FROM marketplace_assets").fetchall())
chk("usermanager" not in {k.lower() for k in rows}, f"TC-50-02 usermanager 미시드")
utils = sorted(k for k, c in rows.items() if c == "utilities")
chk(len(utils) == 5, f"TC-50-02 utilities 5종 ({utils})")
chk(sum(1 for c in rows.values() if c == "security") == 13, "TC-50-02 security 13종")

# TC-50-03/04/05 준비: 시드 고아·사용자 자산·설치 중 고아 삽입
ins_asset = ("INSERT INTO marketplace_assets (tenant_id, asset_key, version, kind, name, category) "
             "VALUES ('default', ?, '1.0.0', 'agent', ?, ?)")
ins_blob = ("INSERT INTO marketplace_asset_blobs (tenant_id, asset_key, version, filename, blob, uploaded_by) "
            "VALUES ('default', ?, '1.0.0', ?, X'00', ?)")
con.execute(ins_asset, ("usermanager", "사용자 관리", "utilities"))
con.execute(ins_blob, ("usermanager", "UserManager.zip", "seed-assets"))
con.execute(ins_asset, ("user-own", "사용자 자산", "mycat"))
con.execute(ins_blob, ("user-own", "user-own.zip", "sup1"))
con.execute(ins_asset, ("inst-orphan", "설치중 고아", "utilities"))
con.execute(ins_blob, ("inst-orphan", "inst-orphan.zip", "seed-assets"))
con.execute("INSERT INTO marketplace_installs (tenant_id, asset_key, version, active) "
            "VALUES ('default', 'inst-orphan', '1.0.0', 1)")
con.commit()
con.close()

out = run_seed()
con = sqlite3.connect(DB)
keys = {r[0] for r in con.execute("SELECT asset_key FROM marketplace_assets").fetchall()}
blob_keys = {r[0] for r in con.execute("SELECT asset_key FROM marketplace_asset_blobs").fetchall()}
con.close()

# TC-50-03: 구 시드 행 정리
chk("usermanager" not in keys and "usermanager" not in blob_keys,
    f"TC-50-03 시드 고아(usermanager) 행·블롭 정리")
chk("시드 고아 정리: usermanager" in out, "TC-50-03 정리 로그 출력")
# TC-50-04: 사용자 등록 자산 유지
chk("user-own" in keys and "user-own" in blob_keys, "TC-50-04 사용자 자산 유지")
# TC-50-05: 설치 중 고아는 건너뜀
chk("inst-orphan" in keys, "TC-50-05 설치 중 고아 유지(건너뜀)")
chk("설치 중" in out and "inst-orphan" in out, "TC-50-05 경고 출력")

print(f"\n{'FAIL ' + str(len(fails)) if fails else 'ALL PASS'}")
sys.exit(1 if fails else 0)
