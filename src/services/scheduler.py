import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.db.session import AsyncSessionLocal
from src.db.models import Product, PriceHistory, ProductSubscription
from src.services.scraper import scrape_product_price
from src.services.email import send_price_drop_email

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_all_product_prices():
    """
    Rendszeresen lefutó feladat: Végigzongorázza az összes terméket,
    lekéri az új árukat, elmenti a történetbe, és ellenőrizve a feliratkozási target price-okat e-mailt küld.
    """
    logger.info("=== Elindult az automatikus árellenőrzés ===")
    
    async with AsyncSessionLocal() as db:
        # 1. Lekérjük az összes regisztrált terméket
        result = await db.execute(select(Product))
        products = result.scalars().all()

        for product in products:
            logger.info(f"Termék ellenőrzése: {product.title} ({product.url})")
            scraped_data = await scrape_product_price(product.url)

            if not scraped_data or scraped_data.get("price") is None:
                logger.warning(f"Nem sikerült az árat kinyerni a termékhez: {product.id}")
                continue

            current_price = scraped_data["price"]
            is_in_stock = scraped_data.get("is_in_stock", True)

            # 2. Elmentjük a PriceHistory táblába az új rekordot
            price_entry = PriceHistory(
                product_id=product.id,
                price=current_price,
                is_in_stock=is_in_stock
            )
            db.add(price_entry)

            # 3. Ellenőrizzük a feliratkozásokat (betöltve a user relációt is)
            sub_query = (
                select(ProductSubscription)
                .options(selectinload(ProductSubscription.user))
                .where(ProductSubscription.product_id == product.id)
            )
            sub_res = await db.execute(sub_query)
            subscriptions = sub_res.scalars().all()

            for sub in subscriptions:
                # Csak akkor küldünk e-mailt, ha:
                # 1. Van célár ÉS a jelenlegi ár alacsonyabb vagy egyenlő nála
                # 2. Még NEM küldtünk e-mailt erről a leárazásról (last_notified_at is None)
                if sub.target_price and current_price <= sub.target_price:
                    if sub.last_notified_at is None:
                        logger.info(
                            f"ÉRTESÍTÉS TRIGGER! User ID {sub.user_id} feliratkozása elérte a célárat! "
                            f"Jelenlegi ár: {current_price} <= Célár: {sub.target_price}"
                        )
                        
                        if sub.user and sub.user.email:
                            sent_success = await send_price_drop_email(
                                to_email=sub.user.email,
                                product_title=product.title or "Nyomon követett termék",
                                old_price=sub.target_price,
                                new_price=current_price,
                                product_url=product.url
                            )
                            
                            # HA SIKERES AZ E-MAIL, AZONNAL ELMENTJÜK AZ ADATBÁZISBA A DÁTUMOT
                            if sent_success:
                                sub.last_notified_at = datetime.now(timezone.utc)
                                await db.commit()  # Azonnali mentés a duplázás megelőzésére
                                logger.info(f"last_notified_at sikeresen frissítve az adatbázisban: {sub.last_notified_at}")
                    else:
                        logger.debug(f"User ID {sub.user_id} már kapott értesítést erről a célárról ({sub.last_notified_at}).")

                # Ha az ár újra a célár fölé emelkedik, nullázzuk a mezőt, hogy a következő leárazáskor ismét küldhessen értesítőt
                elif sub.target_price and current_price > sub.target_price and sub.last_notified_at is not None:
                    sub.last_notified_at = None
                    await db.commit()
        
        await db.commit()
    logger.info("=== Árellenőrzés befejeződött ===")


def start_scheduler():
    """
    Elindítja az APScheduler időzítőt.
    """
    print(">>> [SCHEDULER] A scheduler indítása megtörtént! <<<")
    scheduler.add_job(check_all_product_prices, 'interval', minutes=10, id="price_check_job", replace_existing=True)
    scheduler.start()
    logger.info("APScheduler sikeresen elindult.")