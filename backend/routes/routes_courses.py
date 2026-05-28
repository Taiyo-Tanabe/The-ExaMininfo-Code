from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas
from ..auth import require_roles, get_current_user
from ..functions.functions_courses import (
    list_courses,
    get_course,
    react_to_course,
    create_course,
    update_course,
    delete_course,
)

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=schemas.Page[schemas.CourseOut])
def list_courses_route(
    school_id: int = None,
    q: str = None,
    sort_by: str = "deviation",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return list_courses(db, school_id, q, sort_by, order, skip, limit)


@router.get("/{course_id}", response_model=schemas.CourseOut)
def get_course_route(course_id: int, db: Session = Depends(get_db)):
    return get_course(db, course_id)


@router.post("/{course_id}/react")
def react_to_course_route(
    course_id: int,
    data: schemas.ReactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return react_to_course(db, course_id, data, current_user)


@router.post("/", response_model=schemas.CourseOut)
def create_course_route(
    data: schemas.CourseCreate,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return create_course(db, data)


@router.put("/{course_id}", response_model=schemas.CourseOut)
def update_course_route(
    course_id: int,
    data: schemas.CourseCreate,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return update_course(db, course_id, data)


@router.delete("/{course_id}")
def delete_course_route(
    course_id: int,
    db: Session = Depends(get_db),
    _ = Depends(require_roles(["admin"])),
):
    return delete_course(db, course_id)
