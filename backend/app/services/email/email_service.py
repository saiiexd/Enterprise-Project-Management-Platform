import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger("epmp.email")


class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str) -> None:
        try:
            # Setup message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.MAIL_FROM
            msg["To"] = to_email

            part = MIMEText(html_content, "html")
            msg.attach(part)

            # Send via SMTP
            with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT) as server:
                if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
            logger.info(f"Successfully sent email '{subject}' to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")

    def send_verification_email(self, to_email: str, token: str) -> None:
        verification_link = f"http://localhost:3000/verify-email?token={token}"
        subject = "Verify Your Account - EPMP"
        html_content = f"""
        <html>
            <body>
                <h2>Welcome to Enterprise Project Management Platform!</h2>
                <p>Thank you for registering. Please verify your account by clicking the link below:</p>
                <p><a href="{verification_link}">Verify Account</a></p>
                <p>If you did not sign up for EPMP, please ignore this email.</p>
            </body>
        </html>
        """
        self.send_email(to_email, subject, html_content)

    def send_reset_password_email(self, to_email: str, token: str) -> None:
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        subject = "Reset Your Password - EPMP"
        html_content = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password. You can do so by clicking the link below:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>This link is valid for 1 hour. If you did not request a password reset, please ignore this email.</p>
            </body>
        </html>
        """
        self.send_email(to_email, subject, html_content)


email_service = EmailService()
