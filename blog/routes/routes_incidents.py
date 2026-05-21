from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import schemas
from ..auth import get_current_user
from ..functions.functions_incidents import (
    list_incidents,
    get_incident,
    create_incident,
    update_incident,
    delete_incident,
    react_to_incident,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("/", response_model=schemas.Page[schemas.IncidentOut])
def list_incidents_route(
    school_id: int = None,
    q: str = None,
    school_name: str = None,
    user_id: int = None,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return list_incidents(db, school_id, q, school_name, user_id, sort_by, order, skip, limit)


@router.get("/{incident_id}", response_model=schemas.IncidentOut)
def get_incident_route(incident_id: int, db: Session = Depends(get_db)):
    return get_incident(db, incident_id)


@router.post("/", response_model=schemas.IncidentOut)
def create_incident_route(
    data: schemas.IncidentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_incident(db, data, current_user)


@router.put("/{incident_id}", response_model=schemas.IncidentOut)
def update_incident_route(
    incident_id: int,
    data: schemas.IncidentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_incident(db, incident_id, data, current_user)


@router.delete("/{incident_id}")
def delete_incident_route(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return delete_incident(db, incident_id, current_user)


@router.post("/{incident_id}/react")
def react_to_incident_route(
    incident_id: int,
    data: schemas.ReactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return react_to_incident(db, incident_id, data, current_user)
