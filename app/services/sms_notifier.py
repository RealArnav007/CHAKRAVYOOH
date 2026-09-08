import os
import asyncio
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brevo SMTP config
# Get your SMTP key from: Brevo Dashboard → SMTP & API → SMTP tab
# ---------------------------------------------------------------------------
BREVO_SMTP_HOST  = "smtp-relay.brevo.com"
BREVO_SMTP_PORT  = 587
BREVO_SMTP_LOGIN = os.getenv("BREVO_SMTP_LOGIN")       # your Brevo account email
BREVO_SMTP_KEY   = os.getenv("BREVO_SMTP_KEY")         # SMTP key (NOT your account password)
BREVO_FROM_EMAIL = os.getenv("BREVO_FROM_EMAIL", BREVO_SMTP_LOGIN)
BREVO_FROM_NAME  = os.getenv("BREVO_FROM_NAME", "Project Beacon 🚨")

# Comma-separated list of email addresses to alert
ALERT_EMAIL_RECIPIENTS = [
    e.strip()
    for e in os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")
    if e.strip()
]

# Fast2SMS kept as secondary fallback
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")


async def send_sms_notification(
    origin_id: str,
    summary: str,
    lat: float,
    lon: float,
    escalation: str,
) -> bool:
    """
    Dispatch an alert to emergency contacts.

    Priority order:
      1. Brevo SMTP email (if configured)
      2. Fast2SMS  (if configured)
      3. Console fallback (dev mode)

    Returns True if at least one real alert was dispatched.
    """
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"

    # --- Try Brevo SMTP ---
    if BREVO_SMTP_LOGIN and BREVO_SMTP_KEY and ALERT_EMAIL_RECIPIENTS:
        sent = await asyncio.to_thread(
            _send_brevo_email, origin_id, summary, maps_url, escalation
        )
        if sent:
            logger.info(
                f"Email alert dispatched via Brevo to {len(ALERT_EMAIL_RECIPIENTS)} recipient(s) "
                f"| sos origin={origin_id}"
            )
            return True
        logger.warning("Brevo SMTP failed — trying Fast2SMS fallback")

    # --- Try Fast2SMS ---
    if FAST2SMS_API_KEY:
        import httpx
        sms_body = (
            f"BEACON ALERT [{escalation.upper()}]: {summary} "
            f"Location: {maps_url}"
        )
        phone_numbers = [
            n.strip().lstrip("+91").lstrip("91")
            for n in os.getenv("EMERGENCY_CONTACT_NUMBERS", "").split(",")
            if n.strip()
        ]
        if phone_numbers:
            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.post(
                        "https://www.fast2sms.com/dev/bulkV2",
                        headers={"authorization": FAST2SMS_API_KEY},
                        data={
                            "route": "q",
                            "message": sms_body,
                            "language": "english",
                            "flash": 0,
                            "numbers": ",".join(phone_numbers),
                        },
                    )
                data = resp.json()
                if data.get("return") is True:
                    logger.info(f"SMS dispatched via Fast2SMS | sos origin={origin_id}")
                    return True
                logger.error(f"Fast2SMS error: {data}")
            except Exception as e:
                logger.error(f"Fast2SMS request exception: {e}")

    # --- Console fallback ---
    _console_fallback(escalation, summary, maps_url, origin_id)
    return False


# ---------------------------------------------------------------------------
# Brevo SMTP — runs in a thread (smtplib is synchronous)
# ---------------------------------------------------------------------------

def _send_brevo_email(
    origin_id: str,
    summary: str,
    maps_url: str,
    escalation: str,
) -> bool:
    """Build and send an HTML alert email via Brevo SMTP."""
    subject = f"🚨 BEACON ALERT [{escalation.upper()}] — Emergency SOS Received"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #0A0B0D; color: #f0f0f0; padding: 24px;">
      <div style="max-width: 580px; margin: auto; background: #131519; border-radius: 12px;
                  border: 1px solid #FF5A3C; overflow: hidden;">

        <!-- Header -->
        <div style="background: #FF5A3C; padding: 20px 28px;">
          <h1 style="margin: 0; color: #fff; font-size: 20px; letter-spacing: 1px;">
            🚨 PROJECT BEACON — EMERGENCY ALERT
          </h1>
          <p style="margin: 6px 0 0; color: rgba(255,255,255,0.85); font-size: 13px;">
            Escalation tier: <strong>{escalation.upper()}</strong>
          </p>
        </div>

        <!-- Body -->
        <div style="padding: 24px 28px;">
          <h2 style="color: #FF5A3C; font-size: 15px; margin: 0 0 12px;">AI Dispatch Summary</h2>
          <p style="font-size: 16px; color: #f0f0f0; background: #1e2128; border-left: 3px solid #FF5A3C;
                    padding: 12px 16px; border-radius: 6px; margin: 0 0 20px;">
            {summary}
          </p>

          <h2 style="color: #2DE1C2; font-size: 15px; margin: 0 0 12px;">📍 Location</h2>
          <a href="{maps_url}" style="display: inline-block; background: #2DE1C2; color: #0A0B0D;
             padding: 12px 20px; border-radius: 8px; text-decoration: none; font-weight: bold;
             font-size: 14px;">
            Open on Google Maps →
          </a>

          <p style="margin: 24px 0 0; font-size: 12px; color: #666;">
            Origin device: <code>{origin_id}</code><br>
            This is an automated alert from the Chakravyooh Emergency Intelligence & Operations system.
          </p>
        </div>

        <!-- Footer -->
        <div style="background: #0A0B0D; padding: 14px 28px; border-top: 1px solid #222;">
          <p style="margin: 0; font-size: 11px; color: #444;">
            IIC 3.0 · Chakravyooh · Tropical Cyclone Intelligence & Resilient Operations
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{BREVO_FROM_NAME} <{BREVO_FROM_EMAIL}>"
    msg["To"]      = ", ".join(ALERT_EMAIL_RECIPIENTS)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(BREVO_SMTP_HOST, BREVO_SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(BREVO_SMTP_LOGIN, BREVO_SMTP_KEY)
            server.sendmail(BREVO_FROM_EMAIL, ALERT_EMAIL_RECIPIENTS, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Brevo SMTP error: {e}")
        return False


def _console_fallback(escalation: str, summary: str, maps_url: str, origin_id: str):
    logger.warning(
        "\n" + "=" * 60 + "\n"
        "[ALERT STUB — configure BREVO_SMTP_* env vars to send real alerts]\n"
        f"[ESCALATION] {escalation.upper()}  |  origin={origin_id}\n"
        f"[SUMMARY] {summary}\n"
        f"[LOCATION] {maps_url}\n"
        + "=" * 60
    )
