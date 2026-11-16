
import pytest

from app.observability.sli import (
    calculate_availability,
    calculate_error_rate,
    calculate_event_processing_rate,
)


def test_calculate_error_rate():
    result = calculate_error_rate(1000, 10)
    assert result == 1.0


def test_calculate_availability():
    result = calculate_availability(1000, 999)
    assert result == 99.9


def test_calculate_event_processing_rate():
    result = calculate_event_processing_rate(1000, 950)
    assert result == 95.0


def test_error_rate_with_zero_requests():
    assert calculate_error_rate(0, 0) == 0.0


def test_negative_request_count():
    with pytest.raises(ValueError):
        calculate_error_rate(-100, 10)


def test_failed_requests_exceed_total():
    with pytest.raises(ValueError):
        calculate_error_rate(100, 150)
