
from sqlalchemy import func, select

from app.domain import lease_service
from app.persistence.models import LeaseEvent, OutboxEvent


def test_process_payment_made_event(db_session):
    event = lease_service.process_lease_event(
        db=db_session,
        driver_id="GW1001",
        event_type="payment_made",
    )

    assert event["driver_id"] == "GW1001"
    assert event["event_type"] == "payment_made"
    assert event["event_id"]

    lease = lease_service.get_lease(db_session, "GW1001")
    assert lease["lease_status"] == "active"


def test_process_payment_missed_event(db_session):
    lease_service.process_lease_event(
        db=db_session,
        driver_id="GW1002",
        event_type="payment_missed",
    )

    lease = lease_service.get_lease(db_session, "GW1002")
    assert lease["lease_status"] == "payment_pending"


def test_process_lease_paused_event(db_session):
    lease_service.process_lease_event(
        db=db_session,
        driver_id="GW1003",
        event_type="lease_paused",
    )

    lease = lease_service.get_lease(db_session, "GW1003")
    assert lease["lease_status"] == "paused"


def test_get_lease_returns_none_for_unknown_driver(db_session):
    lease = lease_service.get_lease(db_session, "UNKNOWN")

    assert lease is None


def test_event_is_stored(db_session):
    lease_service.process_lease_event(
        db=db_session,
        driver_id="GW1004",
        event_type="payment_made",
    )

    event_count = db_session.scalar(
        select(func.count()).select_from(LeaseEvent)
    )

    outbox_count = db_session.scalar(
        select(func.count()).select_from(OutboxEvent)
    )

    assert event_count == 1
    assert outbox_count == 1
