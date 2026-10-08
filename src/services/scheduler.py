import logging
from sqlalchemy import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.db.session import AsyncSessionLocal
from src.db.models import Product, PriceHistory, ProductSubscription
from src.services.scraper import scrape_product_price

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_all_product_prices():
    """
    Rendszeresen lefutó feladat: Végigzongorázza az összes terméket,
    lekéri az új árukat, elmenti a történetbe, és ellenőrzi a feliratkozási target price-okat.
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

            # 3. Ellenőrizzük a feliratkozásokat
            sub_query = select(ProductSubscription).where(
                ProductSubscription.product_id == product.id
            )
            sub_res = await db.execute(sub_query)
            subscriptions = sub_res.scalars().all()

            for sub in subscriptions:
                if sub.target_price and current_price <= sub.target_price:
                    logger.info(
                        f"ÉRTESÍTÉS TRIGGER! User ID {sub.user_id} feliratkozása elérte a célárat! "
                        f"Jelenlegi ár: {current_price} Ft <= Célár: {sub.target_price} Ft"
                    )
                    # ITT LEHET MAJD EMAIL/PUSH ÉRTESÍTÉST KÜLDENI!

        await db.commit()
    logger.info("=== Árellenőrzés befejeződött ===")


def start_scheduler():
    """
    Elindítja az APScheduler időzítőt (pl. 30 percenkénti futással).
    """
    print(">>> [SCHEDULER] A scheduler indítása megtörtent! <<<")
    # Teszteléshez 1 percre állítjuk, élesben pl. hours=1 vagy minutes=30
    scheduler.add_job(check_all_product_prices, 'interval', minutes=2, id="price_check_job", replace_existing=True)
    scheduler.start()
    logger.info("APScheduler sikeresen elindult.")