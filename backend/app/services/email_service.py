import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Sends an email using the configured SMTP server.
        Falls back to console logging if SMTP is not configured.
        """
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            logger.info(f"Mock Email sent to {to_email}: {subject}")
            logger.debug(f"Email Content:\\n{html_content}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = to_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())

            logger.info(f"Email successfully sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @staticmethod
    def send_notification_email(
        to_email: str, title: str, message: str, action_url: str = None
    ) -> bool:
        """Helper to send a standard notification email format."""
        action_html = (
            f"<p><a href='{action_url}'>Click here to view</a></p>"
            if action_url
            else ""
        )
        html = f"""
        <html>
            <body>
                <h2>{title}</h2>
                <p>{message}</p>
                {action_html}
                <br/>
                <p>Thanks,<br/>The DevLink Team</p>
            </body>
        </html>
        """
        return EmailService.send_email(to_email, title, html)
