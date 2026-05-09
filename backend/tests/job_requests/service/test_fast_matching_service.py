"""
Unit / integration tests for US-24: Fast Matching Results.

As an end-user, I want matching and booking responses to be returned within
3 seconds, so that I do not experience delays while using the system.

These tests execute against the real PostgreSQL test container so the
timing covers actual query + scoring work, not just in-memory logic.
Each assertion uses a 3-second upper bound (matching the acceptance criterion)
with a conservative 2-second wall-clock budget to leave headroom for CI.
"""
import time
from datetime import date
from decimal import Decimal

from app.models import (
    db, User, UserProfile, CleanerProfile, CleanerAvailability,
    JobRequest, UserRole, ServiceType, JobStatus
)

PERF_BUDGET_SECONDS = 2.0   # stricter than the 3 s acceptance criterion


# ---------------------------------------------------------------------------
# Helpers (mirror the helpers in test_auto_matching_service.py)
# ---------------------------------------------------------------------------

def _user(email, role=UserRole.end_user, is_banned=False):
    u = User(email=email, password_hash="x", role=role, is_banned=is_banned)
    db.session.add(u)
    db.session.flush()
    return u


def _user_profile(user_id, first="Test", last="User"):
    p = UserProfile(user_id=user_id, first_name=first, last_name=last)
    db.session.add(p)
    db.session.flush()
    return p


def _cleaner_profile(user_id, service_type=ServiceType.partial, rate="20.00", exp=0):
    cp = CleanerProfile(
        user_id=user_id,
        service_type=service_type,
        hourly_rate=Decimal(rate),
        years_experience=exp,
    )
    db.session.add(cp)
    db.session.flush()
    return cp


def _availability(cp_id, start_date, end_date, start_time=None, end_time=None):
    slot = CleanerAvailability(
        cleaner_profile_id=cp_id,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
    )
    db.session.add(slot)
    db.session.flush()
    return slot


def _job(end_user_id, service_type=ServiceType.partial, status=JobStatus.pending,
         preferred_date=date(2099, 12, 31)):
    jr = JobRequest(
        end_user_id=end_user_id,
        title="Perf test job",
        description="desc",
        service_type=service_type,
        location="1 Test Road",
        preferred_date=preferred_date,
        status=status,
    )
    db.session.add(jr)
    db.session.flush()
    return jr


# ---------------------------------------------------------------------------
# US-24 tests
# ---------------------------------------------------------------------------

def test_find_matching_cleaners_completes_within_budget_no_cleaners(app):
    """US-24: matching with zero eligible cleaners returns within the time budget."""
    from app.services.matching_service import MatchingService

    with app.app_context():
        end_user = _user("perf_eu1@test.com")
        job = _job(end_user.id)
        db.session.commit()

        start = time.perf_counter()
        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")
        elapsed = time.perf_counter() - start

        assert result["matches"] == []
        assert elapsed < PERF_BUDGET_SECONDS, (
            f"find_matching_cleaners took {elapsed:.3f}s — exceeds {PERF_BUDGET_SECONDS}s budget"
        )


def test_find_matching_cleaners_completes_within_budget_with_multiple_cleaners(app):
    """US-24: matching with 5 eligible cleaners returns within the time budget."""
    from app.services.matching_service import MatchingService

    with app.app_context():
        end_user = _user("perf_eu2@test.com")
        job = _job(end_user.id, preferred_date=date(2099, 6, 15))

        for i in range(5):
            c = _user(f"perf_c{i}@test.com", role=UserRole.cleaner)
            _user_profile(c.id, first=f"Cleaner{i}", last="Perf")
            cp = _cleaner_profile(c.id, rate=str(20 + i * 5), exp=i)
            _availability(cp.id, date(2099, 6, 1), date(2099, 12, 31))

        db.session.commit()

        start = time.perf_counter()
        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")
        elapsed = time.perf_counter() - start

        assert len(result["matches"]) > 0
        assert elapsed < PERF_BUDGET_SECONDS, (
            f"find_matching_cleaners took {elapsed:.3f}s — exceeds {PERF_BUDGET_SECONDS}s budget"
        )


def test_auto_assign_cleaner_completes_within_budget(app):
    """US-24: auto-assign (matching + DB write) completes within the time budget."""
    from app.services.matching_service import MatchingService

    with app.app_context():
        end_user = _user("perf_eu3@test.com")
        job = _job(end_user.id)
        c = _user("perf_assign@test.com", role=UserRole.cleaner)
        _user_profile(c.id, first="Fast", last="Cleaner")
        _cleaner_profile(c.id, rate="20.00", exp=3)
        db.session.commit()

        start = time.perf_counter()
        result = MatchingService.auto_assign_cleaner(job.id, end_user.id, "end_user")
        elapsed = time.perf_counter() - start

        assert result["assigned_cleaner"]["cleaner_id"] == c.id
        assert elapsed < PERF_BUDGET_SECONDS, (
            f"auto_assign_cleaner took {elapsed:.3f}s — exceeds {PERF_BUDGET_SECONDS}s budget"
        )


def test_matching_route_responds_within_budget(client, patch_decode_token, bearer_header, mocker):
    """US-24: the /match HTTP endpoint round-trip responds within the time budget."""
    patch_decode_token(payload={"user_id": 1, "email": "u@test.com", "role": "end_user"})
    mocker.patch(
        "app.services.matching_service.MatchingService.find_matching_cleaners",
        return_value={"job_request_id": 1, "matches": []}
    )

    start = time.perf_counter()
    resp = client.get("/api/job-requests/1/match", headers=bearer_header("ok"))
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    assert elapsed < PERF_BUDGET_SECONDS, (
        f"Match route took {elapsed:.3f}s — exceeds {PERF_BUDGET_SECONDS}s budget"
    )


def test_matching_route_passes_strategy(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 1, "email": "u@test.com", "role": "end_user"})
    mock_svc = mocker.patch(
        "app.services.matching_service.MatchingService.find_matching_cleaners",
        return_value={"job_request_id": 1, "strategy": "lowest_price", "matches": []}
    )

    resp = client.get(
        "/api/job-requests/1/match?strategy=lowest_price",
        headers=bearer_header("ok"),
    )

    assert resp.status_code == 200
    mock_svc.assert_called_once_with(
        1,
        1,
        "end_user",
        strategy_name="lowest_price",
    )


def test_auto_assign_route_passes_strategy(client, patch_decode_token, bearer_header, mocker):
    patch_decode_token(payload={"user_id": 1, "email": "u@test.com", "role": "end_user"})
    mock_svc = mocker.patch(
        "app.services.matching_service.MatchingService.auto_assign_cleaner",
        return_value={
            "message": "Assigned.",
            "job_request": {},
            "assigned_cleaner": {},
            "strategy": "highest_experience",
        }
    )

    resp = client.post(
        "/api/job-requests/1/auto-assign",
        headers=bearer_header("ok"),
        json={"strategy": "highest_experience"},
    )

    assert resp.status_code == 200
    mock_svc.assert_called_once_with(
        1,
        1,
        "end_user",
        strategy_name="highest_experience",
    )


def test_matching_result_returned_not_empty_when_eligible_cleaner_exists(app):
    """US-24: matching response is non-empty within the time budget when a match exists."""
    from app.services.matching_service import MatchingService

    with app.app_context():
        end_user = _user("perf_eu4@test.com")
        job = _job(end_user.id)
        c = _user("perf_eligible@test.com", role=UserRole.cleaner)
        _user_profile(c.id, first="Eligible", last="One")
        _cleaner_profile(c.id, rate="20.00", exp=2)
        db.session.commit()

        start = time.perf_counter()
        result = MatchingService.find_matching_cleaners(job.id, end_user.id, "end_user")
        elapsed = time.perf_counter() - start

        assert len(result["matches"]) == 1
        assert result["matches"][0]["cleaner_id"] == c.id
        assert elapsed < PERF_BUDGET_SECONDS, (
            f"Matching took {elapsed:.3f}s — exceeds {PERF_BUDGET_SECONDS}s budget"
        )
