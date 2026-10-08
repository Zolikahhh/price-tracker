import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.schemas import PriceHistoryResponse
from src.db.models import PriceHistory, Product

router = APIRouter()


@router.get("/{product_id}", response_model=List[PriceHistoryResponse])
async def get_product_price_history(
    product_id: uuid.UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Egy konkrét termék árelőzményeinek lekérése időrendben (legfrissebb elöl).
    """
    # 1. Ellenőrizzük, hogy létezik-e a termék
    product_query = select(Product).where(Product.id == product_id)
    product_res = await db.execute(product_query)
    if not product_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A megadott termék nem található."
        )

    # 2. Árelőzmények lekérése
    history_query = (
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.scraped_at.desc())
        .limit(limit)
    )
    result = await db.execute(history_query)
    return result.scalars().all()