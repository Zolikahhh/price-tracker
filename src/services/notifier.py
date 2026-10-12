import logging
import smtplib
import asyncio
from email.message import EmailMessage
from src.config import settings

logger = logging.getLogger(__name__)


def _send_sync_email(message: EmailMessage):
    """Szinkron e-mail küldő segédfüggvény (külön szálon fut)."""
    if settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)


async def send_price_alert_email(to_email: str, product_title: str, current_price: float, target_price: float) -> bool:
    """Aszinkron wrappelt e-mail küldés a beépített smtplib modullal."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(f"[EMAIL SIMULATION] Értesítés ide: {to_email} | Termék: '{product_title}' | Új ár: {current_price} Ft")
        return True

    message = EmailMessage()
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = f"Árzuhanás értesítő: {product_title}"

    body = f"""
    Szia!

    A(z) '{product_title}' termék ára lecsökkent a beállított célárad alá!

    Jelenlegi ár: {current_price:,.0f} Ft
    Célárad: {target_price:,.0f} Ft

    Nézd meg a webáruházban, mielőtt elkapkodják!

    Üdvözlettel,
    {settings.EMAILS_FROM_NAME}
    """
    message.set_content(body)

    try:
        # Külön szálra szervezzük a szinkron hálózati hívást, hogy ne blokkolja az async event loopot
        await asyncio.to_thread(_send_sync_email, message)
        logger.info(f"Sikeres e-mail küldés ide: {to_email}")
        return True
    except Exception as e:
        logger.error(f"Hiba történt az e-mail küldése során ({to_email}): {str(e)}")
        return False
