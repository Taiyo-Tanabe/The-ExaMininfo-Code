"""
data_raw.csv → PostgreSQL 一括インポート

使い方:
  python scripts/import_db.py

CSVの列: school_name, prefecture, course_name, deviation
  - 学校は name+prefecture でマッチ、なければ自動作成
  - コースは (school_id, name, source) でupsert（既存は偏差値を上書き）

SOURCE_NAME は scrape.py と同じ値にすること。
"""

import csv
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# .env を読み込む
load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

SOURCE_NAME = "momotaro.website"   # scrape.py の SOURCE_NAME と合わせる
INPUT_CSV   = Path(__file__).parent / "data_raw.csv"


def _base_name(name: str) -> str:
    """末尾の括弧を除いた学部名を返す: '生物資源科学部(獣医以外)' → '生物資源科学部'"""
    return re.sub(r'\s*\([^)]+\)\s*$', '', name).strip()


def merge_split_courses(rows: list[dict]) -> list[dict]:
    """
    同一学校・同一学部名で括弧付きサフィックスだけ異なる行を統合する。
    例: '生物資源科学部(獣医以外)' + '生物資源科学部(獣医学科)' → '生物資源科学部'（偏差値は高い方）
    単独でしか存在しない括弧付き名称はそのまま残す。
    """
    # (school_name, prefecture, base_name) でグループ化
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        base = _base_name(row["course_name"].strip())
        key = (row["school_name"].strip(), row["prefecture"].strip(), base)
        groups[key].append(row)

    merged = []
    for (school_name, prefecture, base), group in groups.items():
        if len(group) > 1:
            # 複数エントリ → 偏差値が最大の行をベースに、名称をベース名に統一
            best = max(group, key=lambda r: float(r["deviation"]) if r["deviation"] else 0)
            merged_row = dict(best)
            merged_row["course_name"] = base
            merged.append(merged_row)
        else:
            merged.append(group[0])
    return merged


def main():
    if not INPUT_CSV.exists():
        print(f"CSVが見つかりません: {INPUT_CSV}")
        sys.exit(1)

    with open(INPUT_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("CSVが空です。")
        sys.exit(1)

    print(f"{len(rows)} 件を読み込みました")
    rows = merge_split_courses(rows)
    print(f"{len(rows)} 件に統合しました（同学部の括弧付き分割表記をマージ）")
    print(f"処理開始 (出典: {SOURCE_NAME})")

    engine = create_engine(DATABASE_URL)
    school_cache: dict[tuple[str, str], int] = {}
    new_schools = 0
    upserted    = 0

    with engine.begin() as conn:
        for i, row in enumerate(rows):
            school_name = row["school_name"].strip()
            prefecture  = row["prefecture"].strip()
            course_name = row["course_name"].strip()

            try:
                deviation = float(row["deviation"])
            except ValueError:
                print(f"  [SKIP] 偏差値が数値でない行 {i+2}: {row}")
                continue

            if not school_name or not prefecture or not course_name:
                continue

            # 学校をキャッシュ付きで取得 or 作成
            # name が UNIQUE のため、同名校が別県に存在する場合は既存レコードを使う
            key = school_name
            if key not in school_cache:
                # まず name で検索
                result = conn.execute(
                    text("SELECT id FROM schools WHERE name = :n"),
                    {"n": school_name},
                ).fetchone()

                if result:
                    school_cache[key] = result[0]
                else:
                    # INSERT、name 重複時は DO NOTHING して再取得
                    conn.execute(
                        text(
                            "INSERT INTO schools (name, prefecture) "
                            "VALUES (:n, :p) ON CONFLICT (name) DO NOTHING"
                        ),
                        {"n": school_name, "p": prefecture},
                    )
                    r = conn.execute(
                        text("SELECT id FROM schools WHERE name = :n"),
                        {"n": school_name},
                    ).fetchone()
                    school_cache[key] = r[0]
                    new_schools += 1

            school_id = school_cache[key]

            # コースをupsert
            conn.execute(
                text("""
                    INSERT INTO courses (school_id, name, deviation, source)
                    VALUES (:sid, :name, :dev, :src)
                    ON CONFLICT (school_id, name, source) DO UPDATE
                        SET deviation = EXCLUDED.deviation
                """),
                {
                    "sid":  school_id,
                    "name": course_name,
                    "dev":  deviation,
                    "src":  SOURCE_NAME,
                },
            )
            upserted += 1

            if (i + 1) % 500 == 0:
                print(f"  {i+1}/{len(rows)} 件処理済み...")

    print(f"\n完了:")
    print(f"  新規学校: {new_schools} 校")
    print(f"  コースupsert: {upserted} 件")


if __name__ == "__main__":
    main()
