from abc import ABC, abstractmethod

from app.services.email_service import EmailService


class JobEventListener(ABC):
    @abstractmethod
    def handle(self, event_name: str, job_request):
        pass


class EmailNotificationListener(JobEventListener):
    def handle(self, event_name: str, job_request):
        end_user = job_request.end_user
        cleaner = job_request.cleaner

        end_user_profile = end_user.profile if end_user else None
        cleaner_profile = cleaner.profile if cleaner else None

        end_user_name = (
            f"{end_user_profile.first_name} {end_user_profile.last_name}".strip()
            if end_user_profile else "Customer"
        )
        cleaner_name = (
            f"{cleaner_profile.first_name} {cleaner_profile.last_name}".strip()
            if cleaner_profile else "Cleaner"
        )

        if event_name == "job_confirmed":
            if end_user and end_user.email:
                EmailService.send_booking_confirmation_email(
                    to_email=end_user.email,
                    recipient_name=end_user_name,
                    job_request=job_request,
                    recipient_role="end_user"
                )

            if cleaner and cleaner.email:
                EmailService.send_booking_confirmation_email(
                    to_email=cleaner.email,
                    recipient_name=cleaner_name,
                    job_request=job_request,
                    recipient_role="cleaner"
                )

        elif event_name == "job_cancelled":
            if end_user and end_user.email:
                EmailService.send_booking_cancellation_email(
                    to_email=end_user.email,
                    recipient_name=end_user_name,
                    job_request=job_request,
                    recipient_role="end_user"
                )

            if cleaner and cleaner.email:
                EmailService.send_booking_cancellation_email(
                    to_email=cleaner.email,
                    recipient_name=cleaner_name,
                    job_request=job_request,
                    recipient_role="cleaner"
                )
