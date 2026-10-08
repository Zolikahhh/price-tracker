import logging
import smtplib
from email.message import EmailMessage
from src.config.settings import settings

logger = logging.getLogger(__name__)


def send_price_alert_email(to_email: str, product_title: str, current_price: float, target_price: float, product_url: str):
    """
    Formázott HTML emailt küld a felhasználónak, ha a termék ára a célár alá esett.
    """
    # Ha nincsenek beállítva az SMTP azonosítók, csak szimuláljuk a küldést
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            f"[EMAIL SIMULATION] Értesítés küldése ide: {to_email} | "
            f"Termék: '{product_title}' | Új ár: {current_price} Ft (Célár: {target_price} Ft)"
        )
        return

    msg = EmailMessage()
    msg["Subject"] = f"🎯 Árzuhanás értesítés: {product_title}"
    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    msg["To"] = to_email

    # HTML levelező sablon
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                <h2 style="color: #2c3e50;">A kiszemelt terméked ára lecsökkent! 🎉</h2>
                <p>Szia!</p>
                <p>Jó híreink vannak! A(z) <strong>{product_title}</strong> termék ára elérte a beállított célárodat.</p>
                
                <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Jelenlegi ár:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd; color: #27ae60; font-weight: bold;">{current_price} Ft</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>A te célárod:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{target_price} Ft</td>
                    </tr>
                </table>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="{product_url}" style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Ugrás a termék oldalára</a>
                </div>
            </div>
        </body>
    </html>
    """
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"Sikeres email értesítés elküldve ide: {to_email}")
    except Exception as e:
        logger.error(f"Hiba az email küldése során ({to_email}): {str(e)}")