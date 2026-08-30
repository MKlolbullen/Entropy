from lnkup.responder.correlation import EventCorrelator
from lnkup.responder.events import parse_line


def test_events_from_same_source_correlate():
    correlator = EventCorrelator(window_seconds=60)
    first = parse_line("[LLMNR] request from 192.0.2.4")
    second = parse_line("[LLMNR] request from 192.0.2.4")
    a = correlator.correlate(first)
    b = correlator.correlate(second)
    assert a.correlation_id == b.correlation_id
    assert b.count == 2
