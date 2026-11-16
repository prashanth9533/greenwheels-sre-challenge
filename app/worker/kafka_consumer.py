
import json
import logging
import time
import uuid

from kafka import KafkaConsumer
from kafka.structs import OffsetAndMetadata
from prometheus_client import Counter, Histogram, start_http_server
from sqlalchemy.exc import IntegrityError

from app.persistence.database import SessionLocal
from app.persistence.models import ProcessedEvent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "lease-events"
KAFKA_GROUP_ID = "greenwheels-lease-processor"

# Prometheus metrics
PROCESSED_EVENTS = Counter(
    "lease_events_processed_total",
    "Total number of successfully processed lease events",
)

DUPLICATE_EVENTS = Counter(
    "lease_events_duplicate_total",
    "Total number of duplicate lease events ignored",
)

PROCESSING_ERRORS = Counter(
    "lease_consumer_errors_total",
    "Total number of lease event processing errors",
)

PROCESSING_DURATION = Histogram(
    "lease_event_processing_duration_seconds",
    "Time spent processing lease events",
)


def create_consumer():
    """Create a Kafka consumer with manual offset commits."""
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
        key_deserializer=lambda key: (
            key.decode("utf-8") if key else None
        ),
        max_poll_records=100,
    )


def process_event(payload):
    """Store an event once, ignoring duplicate event IDs."""
    with PROCESSING_DURATION.time():
        event_id = uuid.UUID(payload["event_id"])
        driver_id = payload["driver_id"]
        event_type = payload["event_type"]

        db = SessionLocal()

        try:
            processed_event = ProcessedEvent(
                event_id=event_id,
                driver_id=driver_id,
                event_type=event_type,
            )

            db.add(processed_event)
            db.commit()

            PROCESSED_EVENTS.inc()

            logger.info(
                "Processed event %s for driver %s: %s",
                event_id,
                driver_id,
                event_type,
            )

            return True

        except IntegrityError:
            db.rollback()
            DUPLICATE_EVENTS.inc()

            logger.info("Duplicate event ignored: %s", event_id)

            return False

        except Exception:
            db.rollback()
            PROCESSING_ERRORS.inc()
            logger.exception("Failed to process event %s", event_id)
            raise

        finally:
            db.close()


def process_batch(consumer, records):
    """Process a batch and commit offsets after database success."""
    offsets = {}

    for topic_partition, messages in records.items():
        for message in messages:
            if not isinstance(message.value, dict):
                raise TypeError(
                    f"Invalid event payload at offset {message.offset}"
                )

            process_event(message.value)

            offsets[topic_partition] = max(
                offsets.get(topic_partition, 0),
                message.offset + 1,
            )

    if offsets:
        commit_offsets = {
            topic_partition: OffsetAndMetadata(offset, "")
            for topic_partition, offset in offsets.items()
        }

        consumer.commit(offsets=commit_offsets)

        logger.info(
            "Committed Kafka offsets for %s partition(s)",
            len(commit_offsets),
        )


def main():
    """Continuously consume and process lease events."""
    logger.info("Starting Greenwheels Kafka consumer")

    # Expose worker metrics for Prometheus
    start_http_server(8001)
    logger.info("Prometheus worker metrics available on port 8001")

    consumer = create_consumer()

    try:
        while True:
            records = consumer.poll(
                timeout_ms=1000,
                max_records=100,
            )

            if records:
                process_batch(consumer, records)
            else:
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping Greenwheels Kafka consumer")

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
