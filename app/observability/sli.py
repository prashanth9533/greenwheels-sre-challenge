
def calculate_error_rate(total_requests: int, failed_requests: int) -> float:
    """Calculate API error rate as a percentage."""
    if total_requests < 0 or failed_requests < 0:
        raise ValueError("Request counts cannot be negative")

    if failed_requests > total_requests:
        raise ValueError("Failed requests cannot exceed total requests")

    if total_requests == 0:
        return 0.0

    return (failed_requests / total_requests) * 100


def calculate_availability(total_requests: int, successful_requests: int) -> float:
    """Calculate API availability as a percentage."""
    if total_requests < 0 or successful_requests < 0:
        raise ValueError("Request counts cannot be negative")

    if successful_requests > total_requests:
        raise ValueError("Successful requests cannot exceed total requests")

    if total_requests == 0:
        return 100.0

    return (successful_requests / total_requests) * 100


def calculate_event_processing_rate(
    total_events: int,
    processed_events: int,
) -> float:
    """Calculate successfully processed events as a percentage."""
    if total_events < 0 or processed_events < 0:
        raise ValueError("Event counts cannot be negative")

    if processed_events > total_events:
        raise ValueError("Processed events cannot exceed total events")

    if total_events == 0:
        return 100.0

    return (processed_events / total_events) * 100
