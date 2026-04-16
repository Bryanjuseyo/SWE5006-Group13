"""
Unit tests for email notification behaviour - US-26 through US-29.

US-26: End-user receives booking confirmation email when a cleaner accepts their booking.
US-27: End-user receives cancellation email when a cleaner cancels the booking.
US-28: Cleaner receives booking confirmation email when their booking is confirmed.
US-29: Cleaner receives cancellation email when an end-user cancels the booking.

The tests mock the database layer (JobRequest.query, relationship reloads, db.session)
and assert that EmailService is called with the correct arguments.
"""
import pytest
from app.services.job_request_service import JobRequestService
from app.models import JobStatus

# ---------------------------------------------------------------------------
# Constants shared across all tests
# ---------------------------------------------------------------------------

END_USER_ID = 1
CLEANER_ID = 5
END_USER_EMAIL = "user@test.com"
CLEANER_EMAIL = "cleaner@test.com"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_pending_unassigned_job(mocker):
    """Pending, unassigned job — the state before a cleaner accepts it."""
    mock_end_user = mocker.Mock()
    mock_end_user.id = END_USER_ID
    mock_end_user.email = END_USER_EMAIL

    mock_cleaner = mocker.Mock()
    mock_cleaner.id = CLEANER_ID
    mock_cleaner.email = CLEANER_EMAIL

    mock_job = mocker.Mock()
    mock_job.id = 1
    mock_job.end_user_id = END_USER_ID
    mock_job.cleaner_id = None        # unassigned
    mock_job.status = JobStatus.pending
    mock_job.end_user = mock_end_user
    mock_job.cleaner = mock_cleaner   # relationship resolves after cleaner claims
    mock_job.end_user.profile = None
    mock_job.cleaner.profile = None
    mock_job.to_dict.return_value = {"id": 1, "status": "confirmed"}

    return mock_job, mock_end_user, mock_cleaner


@pytest.fixture
def mock_confirmed_assigned_job(mocker):
    """Confirmed, cleaner-assigned job — the state before a cancellation."""
    mock_end_user = mocker.Mock()
    mock_end_user.id = END_USER_ID
    mock_end_user.email = END_USER_EMAIL

    mock_cleaner = mocker.Mock()
    mock_cleaner.id = CLEANER_ID
    mock_cleaner.email = CLEANER_EMAIL

    mock_job = mocker.Mock()
    mock_job.id = 1
    mock_job.end_user_id = END_USER_ID
    mock_job.cleaner_id = CLEANER_ID
    mock_job.status = JobStatus.confirmed
    mock_job.end_user = mock_end_user
    mock_job.cleaner = mock_cleaner
    mock_job.end_user.profile = None
    mock_job.cleaner.profile = None
    mock_job.to_dict.return_value = {"id": 1, "status": "cancelled"}

    return mock_job, mock_end_user, mock_cleaner


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _patch_job_query(mocker, mock_job):
    """Patch JobRequest.query so filter_by().filter().first() returns mock_job."""
    mock_query = mocker.Mock()
    mock_query.filter_by.return_value.filter.return_value.first.return_value = mock_job
    mocker.patch("app.services.job_request_service.JobRequest.query", mock_query)
    mocker.patch("app.services.job_request_service.db.session")
    mocker.patch(
        "app.services.job_request_service.JobRequestService._get_job_request_with_relationships",
        return_value=mock_job,
    )


def _patch_profiles(
    mocker,
    mock_job,
    end_user_first="Alice", end_user_last="Smith",
    cleaner_first="Bob", cleaner_last="Jones",
):
    """
    Attach relationship profiles directly to the mocked job.
    """
    end_user_profile = mocker.Mock()
    end_user_profile.first_name = end_user_first
    end_user_profile.last_name = end_user_last

    cleaner_profile = mocker.Mock()
    cleaner_profile.first_name = cleaner_first
    cleaner_profile.last_name = cleaner_last

    mock_job.end_user.profile = end_user_profile
    mock_job.cleaner.profile = cleaner_profile
    return end_user_profile, cleaner_profile


def _patch_no_profiles(mocker, mock_job):
    """Ensure neither mocked relationship has a profile attached."""
    mock_job.end_user.profile = None
    mock_job.cleaner.profile = None
    return None


# ===========================================================================
# US-26: End-user receives booking confirmation notification
# ===========================================================================

class TestUS26EndUserBookingConfirmation:

    def test_confirmation_email_sent_to_end_user_when_cleaner_accepts(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-26 (happy path): confirmation email dispatched to end_user."""
        mock_job, _, _ = mock_pending_unassigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        end_user_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "end_user"
        ]
        assert len(end_user_calls) == 1
        assert end_user_calls[0].kwargs["to_email"] == END_USER_EMAIL

    def test_confirmation_email_uses_end_user_profile_name(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-26: recipient_name in email matches the end_user's profile."""
        mock_job, _, _ = mock_pending_unassigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job, end_user_first="Alice", end_user_last="Smith")
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        end_user_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "end_user"
        ]
        assert end_user_calls[0].kwargs["recipient_name"] == "Alice Smith"

    def test_confirmation_email_falls_back_to_customer_when_no_profile(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-26: 'Customer' used as recipient_name when end_user has no profile."""
        mock_job, _, _ = mock_pending_unassigned_job
        _patch_job_query(mocker, mock_job)
        _patch_no_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        end_user_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "end_user"
        ]
        assert end_user_calls[0].kwargs["recipient_name"] == "Customer"

    def test_no_confirmation_email_when_end_user_has_no_email(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-26: email skipped if end_user.email is None."""
        mock_job, mock_end_user, _ = mock_pending_unassigned_job
        mock_end_user.email = None
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        end_user_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "end_user"
        ]
        assert len(end_user_calls) == 0


# ===========================================================================
# US-27: End-user receives cancellation notification
# ===========================================================================

class TestUS27EndUserCancellationNotification:

    def test_cancellation_email_sent_to_end_user_when_cleaner_cancels(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-27 (happy path): cancellation email dispatched to end_user."""
        mock_job, _, _ = mock_confirmed_assigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="cancelled"
        )

        end_user_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "end_user"
        ]
        assert len(end_user_calls) == 1
        assert end_user_calls[0].kwargs["to_email"] == END_USER_EMAIL

    def test_cancellation_email_uses_end_user_profile_name(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-27: recipient_name matches the end_user's profile."""
        mock_job, _, _ = mock_confirmed_assigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job, end_user_first="Alice", end_user_last="Smith")
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="cancelled"
        )

        end_user_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "end_user"
        ]
        assert end_user_calls[0].kwargs["recipient_name"] == "Alice Smith"

    def test_no_cancellation_email_sent_when_preferred_cleaner_declines_pending_job(
        self, mocker, mock_pending_unassigned_job
    ):
        """
        US-27: no cancellation email when a preferred cleaner declines a pending job
        during the priority window — the service returns early without sending emails.
        """
        mock_job, _, _ = mock_pending_unassigned_job
        mock_job.cleaner_id = CLEANER_ID  # preferred cleaner set
        _patch_job_query(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        result = JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="cancelled"
        )

        mock_send.assert_not_called()
        assert "declined" in result["message"].lower()

    def test_no_cancellation_email_when_end_user_has_no_email(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-27: email skipped if end_user.email is None."""
        mock_job, mock_end_user, _ = mock_confirmed_assigned_job
        mock_end_user.email = None
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="cancelled"
        )

        end_user_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "end_user"
        ]
        assert len(end_user_calls) == 0

    def test_cancellation_email_falls_back_to_customer_when_no_profile(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-27: 'Customer' used as recipient_name when end_user has no profile."""
        mock_job, _, _ = mock_confirmed_assigned_job
        _patch_job_query(mocker, mock_job)
        _patch_no_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="cancelled"
        )

        end_user_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "end_user"
        ]
        assert end_user_calls[0].kwargs["recipient_name"] == "Customer"


# ===========================================================================
# US-28: Cleaner receives booking confirmation notification
# ===========================================================================

class TestUS28CleanerBookingConfirmation:

    def test_confirmation_email_sent_to_cleaner_when_booking_confirmed(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-28 (happy path): confirmation email dispatched to cleaner."""
        mock_job, _, _ = mock_pending_unassigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        cleaner_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "cleaner"
        ]
        assert len(cleaner_calls) == 1
        assert cleaner_calls[0].kwargs["to_email"] == CLEANER_EMAIL

    def test_confirmation_email_uses_cleaner_profile_name(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-28: recipient_name in email matches the cleaner's profile."""
        mock_job, _, _ = mock_pending_unassigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job, cleaner_first="Bob", cleaner_last="Jones")
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        cleaner_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "cleaner"
        ]
        assert cleaner_calls[0].kwargs["recipient_name"] == "Bob Jones"

    def test_confirmation_email_falls_back_to_cleaner_when_no_profile(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-28: 'Cleaner' used as recipient_name when cleaner has no profile."""
        mock_job, _, _ = mock_pending_unassigned_job
        _patch_job_query(mocker, mock_job)
        _patch_no_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        cleaner_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "cleaner"
        ]
        assert cleaner_calls[0].kwargs["recipient_name"] == "Cleaner"

    def test_no_confirmation_email_when_cleaner_has_no_email(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-28: email skipped if cleaner.email is None."""
        mock_job, _, mock_cleaner = mock_pending_unassigned_job
        mock_cleaner.email = None
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        cleaner_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "cleaner"
        ]
        assert len(cleaner_calls) == 0

    def test_both_parties_receive_confirmation_email(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-26 + US-28: both end_user and cleaner receive confirmation emails."""
        mock_job, _, _ = mock_pending_unassigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        assert mock_send.call_count == 2
        roles_notified = {c.kwargs["recipient_role"] for c in mock_send.call_args_list}
        assert roles_notified == {"end_user", "cleaner"}


# ===========================================================================
# US-29: Cleaner receives cancellation notification when end-user cancels
# ===========================================================================

class TestUS29CleanerCancellationNotification:

    def test_cancellation_email_sent_to_cleaner_when_end_user_cancels(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-29 (happy path): cancellation email dispatched to cleaner."""
        mock_job, _, _ = mock_confirmed_assigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=END_USER_ID, role="end_user", new_status="cancelled"
        )

        cleaner_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "cleaner"
        ]
        assert len(cleaner_calls) == 1
        assert cleaner_calls[0].kwargs["to_email"] == CLEANER_EMAIL

    def test_cancellation_email_uses_cleaner_profile_name(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-29: recipient_name matches the cleaner's profile."""
        mock_job, _, _ = mock_confirmed_assigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job, cleaner_first="Bob", cleaner_last="Jones")
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=END_USER_ID, role="end_user", new_status="cancelled"
        )

        cleaner_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "cleaner"
        ]
        assert cleaner_calls[0].kwargs["recipient_name"] == "Bob Jones"

    def test_cancellation_email_falls_back_to_cleaner_when_no_profile(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-29: 'Cleaner' used as recipient_name when cleaner has no profile."""
        mock_job, _, _ = mock_confirmed_assigned_job
        _patch_job_query(mocker, mock_job)
        _patch_no_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=END_USER_ID, role="end_user", new_status="cancelled"
        )

        cleaner_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "cleaner"
        ]
        assert cleaner_calls[0].kwargs["recipient_name"] == "Cleaner"

    def test_no_cancellation_email_when_cleaner_has_no_email(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-29: email skipped if cleaner.email is None."""
        mock_job, _, mock_cleaner = mock_confirmed_assigned_job
        mock_cleaner.email = None
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=END_USER_ID, role="end_user", new_status="cancelled"
        )

        cleaner_calls = [
            c for c in mock_send.call_args_list
            if c.kwargs.get("recipient_role") == "cleaner"
        ]
        assert len(cleaner_calls) == 0

    def test_both_parties_receive_cancellation_email_when_end_user_cancels(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-27 + US-29: both end_user and cleaner receive cancellation emails."""
        mock_job, _, _ = mock_confirmed_assigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_send = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=END_USER_ID, role="end_user", new_status="cancelled"
        )

        assert mock_send.call_count == 2
        roles_notified = {c.kwargs["recipient_role"] for c in mock_send.call_args_list}
        assert roles_notified == {"end_user", "cleaner"}

    def test_no_confirmation_email_sent_on_cancellation(
        self, mocker, mock_confirmed_assigned_job
    ):
        """US-29: send_booking_confirmation_email is NOT called when status is cancelled."""
        mock_job, _, _ = mock_confirmed_assigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_confirm = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )
        mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=END_USER_ID, role="end_user", new_status="cancelled"
        )

        mock_confirm.assert_not_called()

    def test_no_cancellation_email_sent_on_confirmation(
        self, mocker, mock_pending_unassigned_job
    ):
        """US-26/28: send_booking_cancellation_email is NOT called when status is confirmed."""
        mock_job, _, _ = mock_pending_unassigned_job
        _patch_job_query(mocker, mock_job)
        _patch_profiles(mocker, mock_job)
        mock_cancel = mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_cancellation_email"
        )
        mocker.patch(
            "app.services.job_request_service.EmailService.send_booking_confirmation_email"
        )

        JobRequestService.update_job_status(
            job_request_id=1, user_id=CLEANER_ID, role="cleaner", new_status="confirmed"
        )

        mock_cancel.assert_not_called()
