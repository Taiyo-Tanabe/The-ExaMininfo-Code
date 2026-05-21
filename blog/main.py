import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, SessionLocal
from . import models
from .routes import routes_schools, routes_courses, routes_incidents, routes_users, routes_posts, routes_settings, routes_reports

app = FastAPI()


@app.on_event("startup")
def migrate_columns():
    from sqlalchemy import text
    with engine.connect() as conn:
        for col in ("occurred_year", "occurred_month", "occurred_day"):
            conn.execute(text(f"ALTER TABLE incidents ADD COLUMN IF NOT EXISTS {col} INTEGER"))
        conn.execute(text("""
            UPDATE incidents
            SET occurred_year  = EXTRACT(YEAR  FROM occurred_date)::INTEGER,
                occurred_month = EXTRACT(MONTH FROM occurred_date)::INTEGER,
                occurred_day   = EXTRACT(DAY   FROM occurred_date)::INTEGER
            WHERE occurred_date IS NOT NULL AND occurred_year IS NULL
        """))
        conn.execute(text(
            "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL"
        ))
        conn.execute(text(
            "ALTER TABLE posts ADD COLUMN IF NOT EXISTS incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL"
        ))
        conn.execute(text(
            "ALTER TABLE posts ADD COLUMN IF NOT EXISTS review_id INTEGER REFERENCES reviews(id) ON DELETE SET NULL"
        ))
        conn.execute(text(
            "ALTER TABLE courses ALTER COLUMN deviation TYPE FLOAT USING deviation::FLOAT"
        ))
        conn.execute(text(
            "ALTER TABLE courses ADD COLUMN IF NOT EXISTS source VARCHAR"
        ))
        conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_course_school_name_source'
                ) THEN
                    ALTER TABLE courses
                    ADD CONSTRAINT uq_course_school_name_source
                    UNIQUE (school_id, name, source);
                END IF;
            END $$
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS blocked_emails (
                id         SERIAL PRIMARY KEY,
                email      VARCHAR UNIQUE NOT NULL,
                blocked_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reports (
                id          SERIAL PRIMARY KEY,
                reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                target_type VARCHAR NOT NULL,
                target_id   INTEGER NOT NULL,
                reason      TEXT,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reviews (
                id         SERIAL PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id)   ON DELETE CASCADE,
                school_id  INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
                rating     INTEGER NOT NULL,
                comment    TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                CONSTRAINT uq_user_school_review UNIQUE (user_id, school_id)
            )
        """))
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_position_x INTEGER NOT NULL DEFAULT 50"
        ))
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_position_y INTEGER NOT NULL DEFAULT 50"
        ))
        conn.commit()


@app.on_event("startup")
def update_stale_site_content():
    from .functions.functions_settings import DEFAULT_CONTENTS
    # 強制更新するキー（大学向けリライト・出典追記）
    FORCE_UPDATE_KEYS = {"hero_title", "home_description", "about", "legal", "site_name"}
    db = SessionLocal()
    try:
        for key, default_value in DEFAULT_CONTENTS.items():
            obj = db.query(models.SiteContent).filter(models.SiteContent.key == key).first()
            if not obj:
                obj = models.SiteContent(key=key, value=default_value)
                db.add(obj)
            elif key in FORCE_UPDATE_KEYS or "ここに" in (obj.value or ""):
                obj.value = default_value
        db.commit()
    finally:
        db.close()

# 開発時: ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
# 本番(同一オリジン配信)は CORS 不要だが念のため設定可能
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

# Static files (avatars, etc.)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(routes_schools.router)
app.include_router(routes_courses.router)
app.include_router(routes_incidents.router)
app.include_router(routes_users.router)
app.include_router(routes_posts.router)
app.include_router(routes_settings.router)
app.include_router(routes_reports.router)

# フロントエンドのビルド成果物を配信（本番用）
# 開発時は Vite dev server が担当するためスキップ
_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dist):
    _assets_dir = os.path.join(_frontend_dist, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        # dist/ 直下にファイルがあればそれを返す（SVGロゴ等）
        candidate = os.path.join(_frontend_dist, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_frontend_dist, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "ExaMininfo API — frontend not built"}
