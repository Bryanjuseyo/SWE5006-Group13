import pytest
from app.services.email_service import EmailService


@pytest.fixture(autouse=True)
def _app_context(app):
    with app.app_context():
        yield


# ---------------------------------------------------------------------------
# _send_email
# ---------------------------------------------------------------------------

def test_send_email_dev_fallback_when_smtp_host_empty(app, capsys):
    app.config["SMTP_HOST"] = ""
    EmailService._send_email("to@test.com", "Hello", "Body text")
    captured = capsys.readouterr()
    assert "DEV FALLBACK" in captured.out


def test_send_email_sends_via_smtp_when_host_set(app, mocker):
    app.config["SMTP_HOST"] = "smtp.test.com"
    try:
        mock_server = mocker.MagicMock()
        mock_smtp = mocker.patch("app.services.email_service.smtplib.SMTP")
        mock_smtp.return_value.__enter__ = mocker.Mock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = mocker.Mock(return_value=False)

        EmailService._send_email("to@test.com", "Subject", "Plain text")

        assert mock_server.sendmail.called
    finally:
        app.config["SMTP_HOST"] = ""


def test_send_email_calls_starttls_and_login_when_credentials_set(app, mocker):
    app.config["SMTP_HOST"] = "smtp.test.com"
    app.config["SMTP_USER"] = "user@test.com"
    app.config["SMTP_PASSWORD"] = "secret"
    try:
        mock_server = mocker.MagicMock()
        mock_smtp = mocker.patch("app.services.email_service.smtplib.SMTP")
        mock_smtp.return_value.__enter__ = mocker.Mock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = mocker.Mock(return_value=False)

        EmailService._send_email("to@test.com", "Subject", "Plain text")

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@test.com", "secret")
        assert mock_server.sendmail.called
    finally:
        app.config["SMTP_HOST"] = ""
        app.config["SMTP_USER"] = ""
        app.config["SMTP_PASSWORD"] = ""


# ---------------------------------------------------------------------------
# send_otp_email
# ---------------------------------------------------------------------------

def test_send_otp_email_dev_fallback_when_smtp_host_empty(app, capsys):
    app.config["SMTP_HOST"] = ""
    EmailService.send_otp_email("to@test.com", "123456")
    captured = capsys.readouterr()
    assert "DEV FALLBACK" in captured.out


def test_send_otp_email_sends_via_smtp_when_host_set(app, mocker):
    app.config["SMTP_HOST"] = "smtp.test.com"
    try:
        mock_server = mocker.MagicMock()
        mock_smtp = mocker.patch("app.services.email_service.smtplib.SMTP")
        mock_smtp.return_value.__enter__ = mocker.Mock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = mocker.Mock(return_value=False)

        EmailService.send_otp_email("to@test.com", "654321", purpose="login")

        assert mock_server.sendmail.called
    finally:
        app.config["SMTP_HOST"] = ""


# ---------------------------------------------------------------------------
# send_booking_confirmation_email
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_job_request(mocker):
    job = mocker.MagicMock()
    job.id = 1
    job.title = "Test Job"
    job.service_type.value = "partial"
    job.location = "Singapore"
    job.preferred_date = "2099-01-01"
    job.preferred_time_start = "09:00"
    job.preferred_time_end = "17:00"
    job.status.value = "confirmed"
    return job


def test_send_booking_confirmation_email_end_user_subject(app, mocker, mock_job_request):
    send_email = mocker.patch.object(EmailService, "_send_email")
    EmailService.send_booking_confirmation_email(
        "user@test.com", "Alice", mock_job_request, "end_user"
    )
    send_email.assert_called_once()
    subject = send_email.call_args[0][1]
    assert "Booking Confirmed" in subject


def test_send_booking_confirmation_email_cleaner_subject(app, mocker, mock_job_request):
    send_email = mocker.patch.object(EmailService, "_send_email")
    EmailService.send_booking_confirmation_email(
        "cleaner@test.com", "Bob", mock_job_request, "cleaner"
    )
    send_email.assert_called_once()
    subject = send_email.call_args[0][1]
    assert "Cleaner Booking Confirmation" in subject


# ---------------------------------------------------------------------------
# send_booking_cancellation_email
# ---------------------------------------------------------------------------

def test_send_booking_cancellation_email_end_user_subject(app, mocker, mock_job_request):
    send_email = mocker.patch.object(EmailService, "_send_email")
    EmailService.send_booking_cancellation_email(
        "user@test.com", "Alice", mock_job_request, "end_user"
    )
    send_email.assert_called_once()
    subject = send_email.call_args[0][1]
    assert subject == "CleanMatch Booking Cancelled"


def test_send_booking_cancellation_email_cleaner_subject(app, mocker, mock_job_request):
    send_email = mocker.patch.object(EmailService, "_send_email")
    EmailService.send_booking_cancellation_email(
        "cleaner@test.com", "Bob", mock_job_request, "cleaner"
    )
    send_email.assert_called_once()
    subject = send_email.call_args[0][1]
    assert "Cleaner Booking Cancelled" in subject
