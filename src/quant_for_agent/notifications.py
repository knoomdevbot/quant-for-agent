from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol


class Notifier(Protocol):
    def send(self, *, subject: str, body: str) -> None: ...


@dataclass(frozen=True)
class EmailNotificationConfig:
    recipients: tuple[str, ...]
    sender: str
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    use_tls: bool = True


class EmailNotifier:
    def __init__(self, config: EmailNotificationConfig):
        if not config.recipients:
            raise ValueError("email notification recipients are required")
        if not config.sender:
            raise ValueError("email notification sender is required")
        if not config.smtp_host:
            raise ValueError("SMTP host is required")
        self.config = config

    def send(self, *, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.config.sender
        message["To"] = ", ".join(self.config.recipients)
        message.set_content(body)

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=20) as smtp:
            if self.config.use_tls:
                smtp.starttls()
            if self.config.smtp_username:
                smtp.login(self.config.smtp_username, self.config.smtp_password or "")
            smtp.send_message(message)
