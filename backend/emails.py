import smtplib
import os

def send_email(
    alert: str,
    receiver: str,
    *,
    sender: str | None = None,
    password: str | None = None,
    smtp_host: str | None = None,
    smtp_port: int | None = None,
):
    sender = (sender or os.getenv("SMTP_SENDER_EMAIL", "")).strip()
    password = (password or os.getenv("SMTP_APP_PASSWORD", "")).strip()
    smtp_host = (smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")).strip()
    smtp_port = int(smtp_port or os.getenv("SMTP_PORT", "587"))

    if not sender or not password:
        raise RuntimeError("SMTP credentials are not configured.")
    if not receiver:
        raise RuntimeError("Receiver email is required.")

    message = f"Subject: Emergency Alert\n\n{alert}"

    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, receiver, message)
    server.quit()