"""
既存DBの分割学部名を統合するスクリプト。

例: '生物資源科学部(獣医以外)' + '生物資源科学部(獣医学科)' → '生物資源科学部'（偏差値は高い方）

使い方:
  python scripts/fix_split_courses.py          # 確認のみ（dry-run）
  python scripts/fix_split_courses.py --apply  # 実際に修正
"""

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).parent.parent / ".env")

# DATABASE_URL が直接指定されていればそちらを優先（Neon など）
DATABASE_URL = os.getenv("DATABASE_URL") or (
    f"postgresql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)


def base_name(name: str) -> str:
    return re.sub(r'\s*\([^)]+\)\s*$', '', name).strip()


def main(apply: bool):
    engine = create_engine(DATABASE_URL)
    fixed = 0

    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, school_id, name, deviation, source FROM courses ORDER BY school_id, name")).fetchall()

        # (school_id, source, base_name) でグループ化
        from collections import defaultdict
        groups: dict[tuple, list] = defaultdict(list)
        for row in rows:
            key = (row.school_id, row.source, base_name(row.name))
            groups[key].append(row)

        for (school_id, source, bname), group in groups.items():
            if len(group) < 2:
                continue
            # 偏差値最大の行を残し、他を削除
            best = max(group, key=lambda r: r.deviation or 0)
            others = [r for r in group if r.id != best.id]

            school_row = conn.execute(text("SELECT name FROM schools WHERE id = :id"), {"id": school_id}).fetchone()
            school_label = school_row.name if school_row else f"id={school_id}"

            print(f"  [{school_label}] {[r.name for r in group]} → '{bname}'（偏差値 {best.deviation}）")

            if apply:
                # best の名前をベース名に更新
                conn.execute(
                    text("UPDATE courses SET name = :n WHERE id = :id"),
                    {"n": bname, "id": best.id},
                )
                # 重複を削除
                for r in others:
                    conn.execute(text("DELETE FROM courses WHERE id = :id"), {"id": r.id})

            fixed += 1

    if fixed == 0:
        print("統合対象のコースは見つかりませんでした。")
    else:
        action = "統合しました" if apply else "件が対象です（--apply で実行）"
        print(f"\n{fixed} グループ{action}")


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    if not apply:
        print("=== DRY RUN（確認のみ）===")
    main(apply)
