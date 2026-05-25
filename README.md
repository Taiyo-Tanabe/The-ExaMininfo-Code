# ExaMininfo（イグザミニンフォー）

**日本中の大学情報を共有できるSNSアプリケーション**

> デモ：https://examininfo.vercel.app/

![トップページ](docs/screenshot.png)

---

## 概要

大学一年時に学校の事件情報をまとめるサイトを制作した経験をベースに、FastAPIの学習を通じてSNS機能へと発展させたWebアプリケーションです。大学の偏差値・学科情報の閲覧から、タイムラインへの投稿・口コミ投稿まで、大学に関する情報を共有できます。

---

## 主な機能

- 大学一覧・詳細表示（偏差値・学科情報）
- **大学名検索（漢字・ひらがな・ローマ字対応）**
- 事案情報の投稿・閲覧
- タイムライン（投稿・リポスト・リプライ）
- 口コミ・レビュー投稿
- ユーザー認証（JWT）
- フォロー機能
- リアクション（いいね）
- 管理者機能

---

## 技術的な工夫

### ローマ字・ひらがな・カタカナ対応の大学名検索

大学名検索で漢字・ひらがな・ローマ字のいずれで入力しても検索できるようにしました。

- ローマ字 → ひらがな変換
- 完全一致・前方一致・部分一致でスコアを付けて優先度を決定
- マッチした文字をハイライト表示

### 偏差値データの自動収集

外部サイトから47都道府県分の偏差値データをスクレイピングし、DBに自動投入するパイプラインを構築しました。サーバーへの負荷を考慮し、リクエスト間隔・同時接続数を制限しています。

### JWT認証

ログイン時にサーバーがトークンを発行してフロントのlocalStorageに保存し、以降のリクエストでトークンを検証することでログイン状態を管理しています。パスワードはbcryptでハッシュ化して保存しています。

---

## 学んだこと

このアプリを開発する過程で、フロントエンド・バックエンド・データベース・クラウドなど、ウェブアプリケーションを構成する各層の役割と連携を実際に体験できました。特に、Renderへのデプロイ時にマイグレーションの失敗でサーバーが起動しないという問題に直面し、原因を特定して修正する経験を通じて、開発環境と本番環境の違いや、デプロイ時のトラブルシューティングの進め方を学びました。

---

## 技術スタック

| 領域 | 技術 |
|------|------|
| フロントエンド | React / Vite / JavaScript |
| バックエンド | Python / FastAPI |
| データベース | PostgreSQL |
| ORM | SQLAlchemy |
| マイグレーション | Alembic |
| 認証 | JWT（python-jose / bcrypt） |
| インフラ | Vercel（フロント）/ Render（バックエンド）/ Neon（DB） |
| コンテナ | Docker / Docker Compose |

---

## アーキテクチャ

```
ユーザー
  ↓
Vercel（React）
  ↓ API通信
Render（FastAPI）
  ↓
Neon（PostgreSQL）
```

---

## セットアップ

### 環境変数

`.env.example` をコピーして `.env` を作成し、値を書き換えてください。

```bash
cp .env.example .env
```

### ローカル起動

**バックエンド：**

```bash
pip install -r requirements.txt
uvicorn blog.main:app --reload --port 8000
```

**フロントエンド：**

```bash
cd frontend
npm install
npm run dev
```

### Dockerで起動

```bash
docker compose up
```

`http://localhost:8000` でアクセスできます。

---

## データ投入

```bash
# スクレイピング（scripts/data_raw.csv に保存）
python scripts/scrape.py

# DBに投入
python scripts/import_db.py
```

---

## プロジェクト構成

```
ExaMIninfo/
├── blog/                        # バックエンド（FastAPI）
│   ├── routes/                  # APIエンドポイント定義
│   │   ├── routes_schools.py
│   │   ├── routes_courses.py
│   │   ├── routes_incidents.py
│   │   ├── routes_users.py
│   │   ├── routes_posts.py
│   │   ├── routes_settings.py
│   │   └── routes_reports.py
│   ├── functions/               # ビジネスロジック
│   │   ├── functions_schools.py
│   │   ├── functions_courses.py
│   │   ├── functions_incidents.py
│   │   ├── functions_users.py
│   │   ├── functions_posts.py
│   │   ├── functions_reviews.py
│   │   ├── functions_settings.py
│   │   └── functions_reports.py
│   ├── models.py                # DBテーブル定義
│   ├── schemas.py               # APIの入出力型定義
│   ├── auth.py                  # JWT認証
│   ├── database.py              # DB接続
│   └── main.py                  # アプリエントリポイント
├── frontend/                    # フロントエンド（React）
│   ├── public/
│   │   └── logo-em.svg
│   ├── src/
│   │   ├── pages/               # 画面
│   │   │   ├── SchoolsPage.jsx
│   │   │   ├── SchoolDetailPage.jsx
│   │   │   ├── PostsPage.jsx
│   │   │   ├── PostDetailPage.jsx
│   │   │   ├── IncidentsPage.jsx
│   │   │   ├── UserProfilePage.jsx
│   │   │   ├── AccountPage.jsx
│   │   │   ├── AvatarEditPage.jsx
│   │   │   ├── AdminPage.jsx
│   │   │   ├── AboutPage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   └── LegalPage.jsx
│   │   ├── components/          # 共通UI部品
│   │   │   ├── Navbar.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── PostCard.jsx
│   │   │   ├── SchoolAutocomplete.jsx
│   │   │   ├── CourseSelect.jsx
│   │   │   └── Pagination.jsx
│   │   ├── utils/
│   │   │   └── fuzzy.js         # ローマ字・ひらがな変換＋あいまい検索
│   │   ├── api.js               # API通信
│   │   ├── AuthContext.jsx      # 認証状態管理
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── vercel.json
│   └── vite.config.js
├── alembic/                     # DBマイグレーション
│   └── versions/
├── scripts/                     # データ収集スクリプト
│   ├── scrape.py                # スクレイピング
│   ├── import_db.py             # DB投入
│   └── data_raw.csv
├── docs/
│   └── screenshot.png
├── docker_start.py              # 起動スクリプト（マイグレーション→uvicorn）
├── build.sh
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── requirements.txt
```
