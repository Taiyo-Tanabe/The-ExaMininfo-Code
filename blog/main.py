import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, SessionLocal
from . import models
from .routes import routes_schools, routes_courses, routes_incidents, routes_users, routes_posts, routes_settings, routes_reports


def update_stale_site_content():
    from .functions.functions_settings import DEFAULT_CONTENTS
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


@asynccontextmanager
async def lifespan(_: FastAPI):
    update_stale_site_content()
    yield


app = FastAPI(lifespan=lifespan)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
if _raw_origins.strip() == "*":
    _allowed_origins = ["*"]
else:
    _allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,  # JWT uses Authorization header, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

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

# React フロントエンド配信
_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(_frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_frontend_dist, "assets")), name="frontend-assets")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(_frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = os.path.join(_frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_frontend_dist, "index.html"))
