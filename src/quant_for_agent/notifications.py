from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol
from urllib.parse import parse_qs, unquote, urlparse


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
    use_ssl: bool = False

    @classmethod
    def from_url(cls, url: str, *, recipients: tuple[str, ...]) -> "EmailNotificationConfig":
        parsed = urlparse(url)
        if parsed.scheme not in {"smtp", "smtps"}:
            raise ValueError("Email SMTP URL must start with smtp:// or smtps://")
        if not parsed.hostname:
            raise ValueError("Email SMTP URL must include a host")
        query = parse_qs(parsed.query)
        username = unquote(parsed.username) if parsed.username else None
        password = unquote(parsed.password) if parsed.password else None
        sender = query.get("from", [username])[0]
        if not sender:
            raise ValueError("Email SMTP URL must include ?from=sender@example.com or a username")
        use_ssl = parsed.scheme == "smtps"
        default_port = 465 if use_ssl else 587
        use_tls = query.get("tls", ["true"])[0].lower() not in {"0", "false", "no", "off"}
        return cls(
            recipients=recipients,
            sender=sender,
            smtp_host=parsed.hostname,
            smtp_port=parsed.port or default_port,
            smtp_username=username,
            smtp_password=password,
            use_tls=use_tls and not use_ssl,
            use_ssl=use_ssl,
        )


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

        client = smtplib.SMTP_SSL if self.config.use_ssl else smtplib.SMTP
        with client(self.config.smtp_host, self.config.smtp_port, timeout=20) as smtp:
            if self.config.use_tls:
                smtp.starttls()
            if self.config.smtp_username:
                smtp.login(self.config.smtp_username, self.config.smtp_password or "")
            smtp.send_message(message)
