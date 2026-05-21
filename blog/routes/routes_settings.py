from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas
from ..auth import require_roles
from ..functions.functions_settings import get_content, update_content

router = APIRouter(prefix="/settings", tags=["Settings"])

ALLOWED_KEYS = {"hero_title", "home_description", "about", "legal"}


@router.get("/{key}", response_model=schemas.SiteContentOut)
def get_content_route(key: str, db: Session = Depends(get_db)):
    if key not in ALLOWED_KEYS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Key not found")
    return get_content(db, key)


@router.put("/{key}", response_model=schemas.SiteContentOut)
def update_content_route(
    key: str,
    data: schemas.SiteContentUpdate,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    if key not in ALLOWED_KEYS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Key not found")
    return update_content(db, key, data)
