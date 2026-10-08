import logging
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

logger = logging.getLogger(__name__)


async def scrape_product_price(url: str) -> Optional[Dict[str, Any]]:
    clean_url = url.strip()

    async with AsyncSession(impersonate="chrome120") as session:
        try:
            response = await session.get(clean_url, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Sikertelen HTTP kérés ({response.status_code}): {clean_url}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            price = None

            # 1. Alza JSON-LD / Structured Data keresés (ez a legmegbízhatóbb az Alzánál!)
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                if script.string and '"price"' in script.string:
                    match = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?', script.string)
                    if match:
                        try:
                            price = float(match.group(1))
                            logger.info(f"Ár megtalálva JSON-LD-ből: {price} Ft")
                            break
                        except ValueError:
                            pass

            # 2. OpenGraph / Schema.org meta tag
            if not price:
                price_meta = (
                    soup.find("meta", property="product:price:amount") or 
                    soup.find("meta", property="og:price:amount") or
                    soup.find("meta", itemprop="price")
                )
                if price_meta and price_meta.get("content"):
                    try:
                        price = float(price_meta["content"].replace(",", "."))
                        logger.info(f"Ár megtalálva Meta tagből: {price} Ft")
                    except ValueError:
                        pass

            # 3. Alza specifikus CSS osztályok (.price-box__price, .price-val, .price_withVat)
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
                        logger.info(f"Ár megtalálva CSS osztályból: {price} Ft")

            if not price:
                logger.warning(f"A HTML letöltődött (200 OK), de nem sikerült kivonni az árat az oldalról: {clean_url}")
                return None

            return {
                "price": price,
                "is_in_stock": True,
                "raw_title": soup.title.string.strip() if soup.title else None
            }

        except Exception as e:
            logger.error(f"Hiba a scraping során ({clean_url}): {str(e)}")
            return None