"""
Alert dispatch for at-risk orders. Two channels supported:
  - Email via SMTP (works with any provider: Gmail app password, SendGrid, etc.)
  - WhatsApp via Twilio's WhatsApp API (sandbox is free and fast to set up)

Set the relevant env vars; if unset, the function logs instead of sending,
so the system still runs end-to-end in a demo without live credentials.
"""
import os
import smtplib
from email.mime.text import MIMEText

import httpx

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")  # e.g. "whatsapp:+14155238886"
ALERT_WHATSAPP_TO = os.getenv("ALERT_WHATSAPP_TO")        # e.g. "whatsapp:+91XXXXXXXXXX"


def send_email_alert(subject: str, body: str) -> bool:
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, ALERT_EMAIL_TO]):
        print(f"[EMAIL ALERT - not configured, logging only]\n{subject}\n{body}")
        return False
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL_TO
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[EMAIL ALERT FAILED] {e}")
        return False


def send_whatsapp_alert(body: str) -> bool:
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_WHATSAPP_FROM, ALERT_WHATSAPP_TO]):
        print(f"[WHATSAPP ALERT - not configured, logging only]\n{body}")
        return False
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    try:
        resp = httpx.post(
            url,
            data={
                "From": TWILIO_WHATSAPP_FROM,
                "To": ALERT_WHATSAPP_TO,
                "Body": body,
            },
            auth=(TWILIO_SID, TWILIO_AUTH),
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"[WHATSAPP ALERT FAILED] {e}")
        return False


def dispatch_breach_alert(order_number: str, risk_score: float, status: str, sla_deadline: str):
    subject = f"SLA Breach Risk: Order {order_number}"
    body = (
        f"Order {order_number} is at risk of breaching its SLA.\n"
        f"Current stage: {status}\n"
        f"Predicted breach risk: {risk_score * 100:.0f}%\n"
        f"SLA deadline: {sla_deadline}\n"
        f"Please review and expedite if needed."
    )
    email_sent = send_email_alert(subject, body)
    wa_sent = send_whatsapp_alert(body)
    return email_sent or wa_sent
