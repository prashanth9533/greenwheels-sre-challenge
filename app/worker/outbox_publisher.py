
import json
import logging
import time
from datetime import UTC, datetime

from kafka import KafkaProducer
from sqlalchemy import select

from app.persistence.database import SessionLocal
from app.persistence.models import OutboxEvent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "lease-events"

BATCH_SIZE = 100
POLL_INTERVAL_SECONDS = 5


def create_producer():
    """Create and configure the Kafka producer."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8"),
        acks="all",
        retries=5,
    )


def publish_pending_events(producer):
    """Read pending outbox events and publish them to Kafka."""
    db = SessionLocal()

    try:
        statement = (
            select(OutboxEvent)
            .where(OutboxEvent.status == "pending")
            .order_by(OutboxEvent.created_at)
            .limit(BATCH_SIZE)
        )

        events = db.scalars(statement).all()

        for event in events:
            event_id = event.id

            try:
                payload = event.payload
                driver_id = payload["driver_id"]

                producer.send(
                    KAFKA_TOPIC,
                    key=driver_id,
                    value=payload,
                ).get(timeout=10)

                event.status = "published"
                event.published_at = datetime.now(UTC)

                db.commit()

                logger.info(
                    "Published outbox event %s for driver %s",
                    event_id,
                    driver_id,
                )

            except Exception as exc:
                db.rollback()

                failed_event = db.get(OutboxEvent, event_id)

                if failed_event is not None:
                    failed_event.attempts += 1
                    failed_event.last_error = str(exc)[:1000]
                    db.commit()

                logger.exception(
                    "Failed to publish outbox event %s",
                    event_id,
                )

    finally:
        db.close()


def main():
    """Continuously publish pending outbox events."""
    logger.info("Starting Greenwheels outbox publisher")

    producer = create_producer()

    try:
        while True:
            publish_pending_events(producer)
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Stopping Greenwheels outbox publisher")

    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
