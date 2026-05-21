from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas
from ..auth import get_current_user
from ..functions.functions_posts import (
    list_posts,
    get_post,
    create_post,
    update_post,
    delete_post,
    list_all_reposts,
    list_reposts,
    create_repost,
    update_repost,
    delete_repost,
    react,
)

router = APIRouter(tags=["Posts"])


@router.get("/reposts/", response_model=schemas.Page[schemas.RepostOut])
def list_all_reposts_route(
    user_id: int = None,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return list_all_reposts(db, user_id, sort_by, order, skip, limit)


@router.get("/posts/", response_model=schemas.Page[schemas.PostOut])
def list_posts_route(
    school_id: int = None,
    q: str = None,
    school_name: str = None,
    user_id: int = None,
    incident_id: int = None,
    review_id: int = None,
    reply_to_id: int = None,
    top_level_only: bool = False,
    replies_only: bool = False,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return list_posts(db, school_id, q, school_name, user_id, incident_id, review_id, reply_to_id, top_level_only, replies_only, sort_by, order, skip, limit)


@router.get("/posts/{post_id}", response_model=schemas.PostOut)
def get_post_route(post_id: int, db: Session = Depends(get_db)):
    return get_post(db, post_id)


@router.post("/posts/", response_model=schemas.PostOut)
def create_post_route(
    data: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_post(db, data, current_user)


@router.put("/posts/{post_id}", response_model=schemas.PostOut)
def update_post_route(
    post_id: int,
    data: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_post(db, post_id, data, current_user)


@router.delete("/posts/{post_id}")
def delete_post_route(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_post(db, post_id, current_user)


@router.get("/posts/{post_id}/reposts", response_model=schemas.Page[schemas.RepostOut])
def list_reposts_route(
    post_id: int,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return list_reposts(db, post_id, sort_by, order, skip, limit)


@router.post("/posts/{post_id}/reposts", response_model=schemas.RepostOut)
def create_repost_route(
    post_id: int,
    data: schemas.RepostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_repost(db, post_id, data, current_user)


@router.put("/reposts/{repost_id}", response_model=schemas.RepostOut)
def update_repost_route(
    repost_id: int,
    data: schemas.RepostUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_repost(db, repost_id, data, current_user)


@router.delete("/reposts/{repost_id}")
def delete_repost_route(
    repost_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_repost(db, repost_id, current_user)


@router.post("/posts/{post_id}/react")
def react_to_post_route(
    post_id: int,
    data: schemas.ReactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return react(db, "post", post_id, data, current_user)


@router.post("/reposts/{repost_id}/react")
def react_to_repost_route(
    repost_id: int,
    data: schemas.ReactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return react(db, "repost", repost_id, data, current_user)
