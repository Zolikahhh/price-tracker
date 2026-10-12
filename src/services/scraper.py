import logging
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Megtisztítja az URL-t, és Amazon esetén felparaméterezi az EUR valutára."""
    clean_url = url.strip()

    if "amazon." in clean_url:
        asin_match = re.search(r"(?:/dp/|/gp/product/|/)([A-Z0-9]{10})(?:[/?]|$)", clean_url)
        if asin_match:
            asin = asin_match.group(1)
            domain_match = re.search(r"https?://(?:www\.)?(amazon\.[a-z.]+)", clean_url)
            domain = domain_match.group(1) if domain_match else "amazon.de"
            # Kikényszerítjük a currency=EUR és nyelv beállításokat az URL paraméterekben
            clean_url = f"https://{domain}/dp/{asin}?currency=EUR&language=en_GB"

    return clean_url


async def scrape_product_price(url: str) -> Optional[Dict[str, Any]]:
    clean_url = normalize_url(url)

    # Amazon számára kért sütik és fejlécek az EUR valuta rögzítéséhez
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9,de-DE;q=0.8,de;q=0.7",
        "Accept": "text/html,application/xhtml+xml,xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }
    
    cookies = {
        "i18n-prefs": "EUR",
        "lc-acbde": "en_GB",
    }

    async with AsyncSession(impersonate="chrome120") as session:
        try:
            response = await session.get(clean_url, headers=headers, cookies=cookies, timeout=25)

            if response.status_code != 200:
                logger.warning(f"Sikertelen HTTP kérés ({response.status_code}): {clean_url}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            price: Optional[float] = None

            # --- A) AMAZON SPECIFIKUS LOGIKA ---
            if "amazon." in clean_url:
                amazon_price_elem = (
                    soup.select_one("#corePrice_feature_div .a-price .a-offscreen") or
                    soup.select_one("#corePriceDisplay_desktop_feature_div .a-price .a-offscreen") or
                    soup.select_one("#apex_desktop .a-price .a-offscreen") or
                    soup.select_one("#price_inside_buybox") or
                    soup.find("span", id="priceblock_dealprice") or
                    soup.find("span", id="priceblock_ourprice") or
                    soup.select_one("span.a-price span.a-offscreen")
                )

                if amazon_price_elem:
                    raw_price_str = amazon_price_elem.text.strip()
                    logger.info(f"Nyers Amazon ár szöveg: '{raw_price_str}'")

                    # 1. Ha Forintban adja vissza a válasz (HUF / Ft)
                    # 1. Ha Forintban adja vissza a válasz (HUF / Ft)
                    if "HUF" in raw_price_str or "Ft" in raw_price_str:
                        # Eltávolítjuk a betűket és a vesszőt (ezres elválasztót)
                        clean_str = raw_price_str.replace(",", "")
                        clean_str = re.sub(r"[^\d\.]", "", clean_str)  # Csak számjegyek és tizedespont marad
                        if clean_str:
                            price = float(clean_str)
                            # Kerekíthetjük is egész forintra, ha szeretnénk: price = round(price)
                            logger.info(f"Sikeresen feldolgozott Amazon HUF ár: {price} Ft")
                    else:
                        # 2. Ha Euróban adja vissza (pl. "€60.49" vagy "60,49 €")
                        clean_str = re.sub(r"[^\d,\.]", "", raw_price_str)
                        if "," in clean_str and "." in clean_str:
                            clean_str = clean_str.replace(".", "").replace(",", ".")
                        elif "," in clean_str:
                            clean_str = clean_str.replace(",", ".")
                        
                        if clean_str:
                            price = float(clean_str)
                            logger.info(f"Sikeresen feldolgozott Amazon EUR ár: {price} €")

            # --- B) ALZA / EGYÉB OLDALAK (Fallback & JSON-LD) ---
            if not price:
                scripts = soup.find_all("script", type="application/ld+json")
                for script in scripts:
                    if script.string and '"price"' in script.string:
                        match = re.search(r'"price"\s*:\s*"?(\d+(?:[\.,]\d+)?)"?', script.string)
                        if match:
                            try:
                                price = float(match.group(1).replace(",", "."))
                                logger.info(f"Ár megtalálva JSON-LD-ből: {price}")
                                break
                            except ValueError:
                                pass

            if not price:
                price_elem = (
                    soup.find("span", class_="price-box__price") or 
                    soup.find("span", class_="price-val") or
                    soup.find("span", class_="bigPrice") or
                    soup.find("span", class_="price_withVat")
                )
                if price_elem:
                    clean_price_str = "".join(filter(str.isdigit, price_elem.text))
                    if clean_price_str:
                        price = float(clean_price_str)
                        logger.info(f"Ár megtalálva Alza CSS osztályból: {price} Ft")

            if not price:
                logger.warning(f"A HTML letöltődött (200 OK), de nem sikerült kivonni az árat: {clean_url}")
                return None

            return {
                "price": price,
                "is_in_stock": True,
                "raw_title": soup.title.string.strip() if soup.title else None
            }

        except Exception as e:
            logger.error(f"Hiba a scraping során ({clean_url}): {str(e)}")
            return None