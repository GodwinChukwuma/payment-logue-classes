from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings

logger = logging.getLogger("wallet_audit")

def send_email_verification(to_email: str, full_name: str, token: str) -> bool:
    subject = "Verify your email wallet API"
    body_text = (
        f"Hi {full_name},\n\n"
        f"Your email verification code is:\n\n  {token}\n\n"
        f"POST this to /api/wallet/verify/email/confirm/ with the field 'token'.\n\n"
        f"This code expires in 24 hours.\n\nWallet API"
    )
    body_html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:2rem">
      <h2 style="margin-bottom:0.5rem">Verify your email</h2>
      <p>Hi <strong>{full_name}</strong>,</p>
      <p>Use the code below to verify your email address:</p>
      <div style="font-size:2rem;font-weight:700;letter-spacing:0.3em;
                  background:#f4f4f4;padding:1rem 2rem;border-radius:8px;
                  display:inline-block;margin:1rem 0">{token}</div>
      <p style="color:#666;font-size:13px">
        POST to <code>/api/wallet/verify/email/confirm/</code> with <code>{{"token":"{token}"}}</code>
      </p>
      <p style="color:#999;font-size:12px">Expires in 24 hours.</p>
    </div>"""
    return _send(to_email, subject, body_html, body_text)

def send_phone_verification(to_email: str, full_name: str, code: str, phone: str) -> bool:
    """
    No SMS sandbox available, so we send the otp to the user's email instead.
    """
    subject = "Your phone verification OTP for wallet API"
    body_text = (
        f"Hi {full_name},\n\n"
        f"Your phone verification OTP for {phone} is:\n\n  {code}\n\n"
        f"POST this to /api/wallet/verify/phone/confirm/ with the field 'code'.\n\n"
        f"This code expires in 10 minutes.\n\nWallet API"
    )
    body_html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:2rem">
      <h2>Phone verification OTP</h2>
      <p>Hi <strong>{full_name}</strong>,</p>
      <p>Your OTP for <strong>{phone}</strong> is:</p>
      <div style="font-size:2rem;font-weight:700;letter-spacing:0.5em;
                  background:#f4f4f4;padding:1rem 2rem;border-radius:8px;
                  display:inline-block;margin:1rem 0">{code}</div>
      <p style="color:#666;font-size:13px">
        POST to <code>/api/wallet/verify/phone/confirm/</code> with <code>{{"code":"{code}"}}</code>
      </p>
      <p style="color:#999;font-size:12px">Expires in 10 minutes.</p>
    </div>"""
    return _send(to_email, subject, body_html, body_text)

def _send(to_email: str, subject: str, body_html: str, body_text: str) -> bool:
    """
    Send one email via mailtrap SMTP
    Return True on success
    Call logs and continue
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))
    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            smtp.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        return True
    except Exception as exc:
        logger.error("email.send_failed", extra={"to": to_email, "error": repr(exc)})
        return False
