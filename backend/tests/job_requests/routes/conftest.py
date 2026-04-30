"""
Shared constants for job request route tests.
"""

FUTURE_DATE = "2099-12-31"
PAST_DATE = "2020-01-01"

VALID_PAYLOAD = {
    "title": "House cleaning",
    "service_type": "full",
    "location": "123 Ang Mo Kio Street",
    "preferred_date": FUTURE_DATE,
}
