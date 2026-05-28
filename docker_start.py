"""
起動スクリプト（Docker / Render 共用）。
- 新規DB: create_all でテーブルを全作成 → alembic stamp head
- 既存DB: alembic upgrade head で差分マイグレーションのみ実行
PORT 環境変数が設定されていれば使用（Render）、なければ 8000（Docker）。
"""
import os
import subprocess
from sqlalchemy import text
from backend.database import engine
from backend import models

with engine.connect() as conn:
    row = conn.execute(
        text("SELECT to_regclass('public.alembic_version')")
    ).scalar()
    alembic_initialized = row is not None

if not alembic_initialized:
    print("=== 新規DB: テーブルを作成します ===")
    models.Base.metadata.create_all(bind=engine)
    print("=== alembic を head にスタンプします ===")
    subprocess.run(["alembic", "stamp", "head"], check=True)
else:
    print("=== 既存DB: alembic upgrade head を実行します ===")
    subprocess.run(["alembic", "upgrade", "head"], check=True)

port = os.getenv("PORT", "8000")
print(f"=== uvicorn を起動します (port={port}) ===")
subprocess.run(
    ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", port],
    check=True,
)
