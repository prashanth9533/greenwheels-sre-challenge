
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.domain.lease_service import get_lease, process_lease_event
from app.persistence.database import get_db

router = APIRouter()
logger = logging.getLogger("greenwheels")


class LeaseEventRequest(BaseModel):
    driver_id: str = Field(min_length=1)
    event_type: Literal["payment_made", "payment_missed", "lease_paused"]


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "greenwheels-fleet-lease-service",
    }


@router.get("/leases/{driver_id}")
def read_lease(
    driver_id: str,
    db: Annotated[Session, Depends(get_db)],
):
    lease = get_lease(db, driver_id)

    if lease is None:
        raise HTTPException(status_code=404, detail="Lease not found")

    return lease


@router.post("/leases/events", status_code=202)
def create_lease_event(
    event: LeaseEventRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    
):
    request.state.driver_id = event.driver_id
    request.state.event_type = event.event_type

    result = process_lease_event(
        db=db,
        driver_id=event.driver_id,
        event_type=event.event_type,
    )

    return {
        "message": "Lease event accepted",
        "event": result,
    }

