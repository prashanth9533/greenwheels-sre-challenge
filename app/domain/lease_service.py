
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import Lease, LeaseEvent, OutboxEvent


def get_lease(db: Session, driver_id: str):
    """Retrieve a driver's lease from PostgreSQL."""
    statement = select(Lease).where(Lease.driver_id == driver_id)
    lease = db.execute(statement).scalar_one_or_none()

    if lease is None:
        return None

    return {
        "driver_id": lease.driver_id,
        "lease_status": lease.lease_status,
        "payment_cycle": lease.payment_cycle,
    }


def process_lease_event(
    db: Session,
    driver_id: str,
    event_type: str,
):
    """Persist a lease event and its Kafka outbox record atomically."""

    with db.begin():
        # Find the driver's lease.
        statement = select(Lease).where(Lease.driver_id == driver_id)
        lease = db.execute(statement).scalar_one_or_none()

        # Create a default lease if this driver is new.
        if lease is None:
            lease = Lease(
                driver_id=driver_id,
                lease_status="active",
                payment_cycle="monthly",
            )
            db.add(lease)
            db.flush()

        # Update the lease status.
        if event_type == "payment_made":
            lease.lease_status = "active"
        elif event_type == "payment_missed":
            lease.lease_status = "payment_pending"
        elif event_type == "lease_paused":
            lease.lease_status = "paused"

        lease.updated_at = datetime.now(UTC)

        # Create the event record.
        event_id = uuid4()
        event_time = datetime.now(UTC)

        event = LeaseEvent(
            event_id=event_id,
            driver_id=driver_id,
            event_type=event_type,
            event_time=event_time,
        )
        db.add(event)
        db.flush()

        # Create an outbox record for asynchronous Kafka publishing.
        payload = {
            "event_id": str(event_id),
            "driver_id": driver_id,
            "event_type": event_type,
            "event_time": event_time.isoformat(),
        }

        outbox_event = OutboxEvent(
            event_id=event_id,
            payload=payload,
            status="pending",
            attempts=0,
        )
        db.add(outbox_event)

    return payload
