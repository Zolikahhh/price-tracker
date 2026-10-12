import logging
import os
from email.message import EmailMessage
import aiosmtplib

logger = logging.getLogger(__name__)

# Környezeti változók beolvasása
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAILS_FROM_EMAIL = os.getenv("EMAILS_FROM_EMAIL", SMTP_USER)
EMAILS_FROM_NAME = os.getenv("EMAILS_FROM_NAME", "Price Tracker")


async def send_price_drop_email(to_email: str, product_title: str, old_price: float, new_price: float, product_url: str):
    """E-mail értesítő küldése árcsökkenés esetén."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP hitelesítési adatok hiányoznak, az e-mail nem került kiküldésre.")
        return False

    message = EmailMessage()
    message["From"] = f"{EMAILS_FROM_NAME} <{EMAILS_FROM_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = f"📉 Árcsökkenés! {product_title}"

    # HTML e-mail törzs
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                <h2 style="color: #2c3e50;">Leárazást találtunk! 🎉</h2>
                <p>Egy általad követett termék ára lecsökkent:</p>
                <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #27ae60; margin: 20px 0;">
                    <h3 style="margin-top: 0;">{product_title}</h3>
                    <p style="margin: 5px 0;">Régi ár: <del style="color: #e74c3c;">{old_price:,} Ft / €</del></p>
                    <p style="margin: 5px 0; font-size: 18px; font-weight: bold; color: #27ae60;">Új ár: {new_price:,} Ft / €</p>
                </div>
                <p>
                    <a href="{product_url}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Megtekintés a webáruházban
                    </a>
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
                <p style="font-size: 12px; color: #7f8c8d;">Ezt az üzenetet az automatikus Price Tracker rendszered küldte.</p>
            </div>
        </body>
    </html>
    """

    message.add_alternative(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True
        )
        logger.info(f"Értesítő e-mail sikeresen elküldve a következő címre: {to_email}")
        return True
    except Exception as e:
        logger.error(f"Hiba az e-mail küldése során ({to_email}): {str(e)}")
        return False