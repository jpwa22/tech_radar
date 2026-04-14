from __future__ import annotations

import smtplib
from email.message import EmailMessage

from config import (
    EMAIL_FROM,
    EMAIL_SUBJECT,
    EMAIL_TO,
    SMTP_HOST,
    SMTP_PASS,
    SMTP_PORT,
    SMTP_USER,
    smtp_configured,
)


def send_report_email(html_report: str, logger) -> bool:
    if not smtp_configured():
        logger.error("SMTP nao configurado. Verifique o arquivo .env.")
        return False

    message = EmailMessage()
    message["Subject"] = EMAIL_SUBJECT
    message["From"] = EMAIL_FROM
    message["To"] = EMAIL_TO
    message.set_content("Seu cliente de e-mail nao suporta HTML.")
    message.add_alternative(html_report, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(message)
        logger.info("E-mail enviado com sucesso para %s", EMAIL_TO)
        return True
    except Exception as exc:
        logger.exception("Falha ao enviar e-mail: %s", exc)
        return False
