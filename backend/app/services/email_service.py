import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


class EmailService:
    @staticmethod
    def _send_email(to_email: str, subject: str, text: str, html: str = None):
        host = current_app.config.get("SMTP_HOST", "")

        if not host:
            print("\n[EMAIL SERVICE - DEV FALLBACK]")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(text)
            print("[END EMAIL]\n")
            return

        port = current_app.config.get("SMTP_PORT", 587)
        user = current_app.config.get("SMTP_USER", "")
        password = current_app.config.get("SMTP_PASSWORD", "")
        from_addr = current_app.config.get("SMTP_FROM", "noreply@cleanmatch.com")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_email

        msg.attach(MIMEText(text, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            if user and password:
                server.starttls()
                server.login(user, password)
            server.sendmail(from_addr, to_email, msg.as_string())

    @staticmethod
    def send_otp_email(to_email: str, otp: str, purpose: str = "verification"):
        host = current_app.config.get("SMTP_HOST", "")

        if not host:
            print("\n[EMAIL SERVICE - DEV FALLBACK]")
            print(f"  To:      {to_email}")
            print(f"  Purpose: {purpose}")
            print(f"  OTP:     {otp}")
            print("[END EMAIL]\n")
            return

        port = current_app.config.get("SMTP_PORT", 587)
        user = current_app.config.get("SMTP_USER", "")
        password = current_app.config.get("SMTP_PASSWORD", "")
        from_addr = current_app.config.get("SMTP_FROM", "noreply@cleanmatch.com")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your CleanMatch Verification Code"
        msg["From"] = from_addr
        msg["To"] = to_email

        text = (
            f"Your CleanMatch OTP code for {purpose} is: {otp}\n"
            f"This code expires in 5 minutes.\n\n"
            f"If you did not request this code, please ignore this email."
        )
        html = f"""
        <html>
          <body style="font-family: sans-serif; max-width: 480px; margin: auto;">
            <h2 style="color: #0d6efd;">CleanMatch Verification Code</h2>
            <p>Your OTP code for <strong>{purpose}</strong> is:</p>
            <div style="font-size: 2rem; font-weight: bold; letter-spacing: 8px;
                        color: #0d6efd; padding: 16px 0;">{otp}</div>
            <p style="color: #6c757d;">This code expires in 5 minutes.</p>
            <p style="color: #6c757d; font-size: 0.875rem;">
              If you did not request this code, please ignore this email.
            </p>
          </body>
        </html>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            if user and password:
                server.starttls()
                server.login(user, password)
            server.sendmail(from_addr, to_email, msg.as_string())

    @staticmethod
    def send_booking_confirmation_email(to_email: str, recipient_name: str, job_request, recipient_role: str):
        if recipient_role == "end_user":
            subject = "CleanMatch Booking Confirmed"
            text = f"""Hello {recipient_name},

Your booking has been confirmed.

Booking ID: {job_request.id}
Title: {job_request.title}
Service Type: {job_request.service_type.value}
Location: {job_request.location}
Date: {job_request.preferred_date}
Start Time: {job_request.preferred_time_start or 'Not specified'}
End Time: {job_request.preferred_time_end or 'Not specified'}
Status: {job_request.status.value}

Thank you,
CleanMatch
"""
        else:
            subject = "CleanMatch Cleaner Booking Confirmation"
            text = f"""Hello {recipient_name},

A booking has been confirmed and assigned to you.

Booking ID: {job_request.id}
Title: {job_request.title}
Service Type: {job_request.service_type.value}
Location: {job_request.location}
Date: {job_request.preferred_date}
Start Time: {job_request.preferred_time_start or 'Not specified'}
End Time: {job_request.preferred_time_end or 'Not specified'}
Status: {job_request.status.value}

Thank you,
CleanMatch
"""

        EmailService._send_email(to_email, subject, text)

    @staticmethod
    def send_booking_cancellation_email(to_email: str, recipient_name: str, job_request, recipient_role: str):
        if recipient_role == "end_user":
            subject = "CleanMatch Booking Cancelled"
            text = f"""Hello {recipient_name},

Your booking has been cancelled.

Booking ID: {job_request.id}
Title: {job_request.title}
Service Type: {job_request.service_type.value}
Location: {job_request.location}
Date: {job_request.preferred_date}
Start Time: {job_request.preferred_time_start or 'Not specified'}
End Time: {job_request.preferred_time_end or 'Not specified'}
Status: {job_request.status.value}

Thank you,
CleanMatch
"""
        else:
            subject = "CleanMatch Cleaner Booking Cancelled"
            text = f"""Hello {recipient_name},

A booking assigned to you has been cancelled.

Booking ID: {job_request.id}
Title: {job_request.title}
Service Type: {job_request.service_type.value}
Location: {job_request.location}
Date: {job_request.preferred_date}
Start Time: {job_request.preferred_time_start or 'Not specified'}
End Time: {job_request.preferred_time_end or 'Not specified'}
Status: {job_request.status.value}

Thank you,
CleanMatch
"""

        EmailService._send_email(to_email, subject, text)
