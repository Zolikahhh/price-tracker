from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.session import get_db  # Vagy ahol a get_db függőséged található
from src.db.models import Product  # Az adatbázis (SQLAlchemy) modeled

# ... meglévő kódsorok és végpontok ...


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Termék törlése az adatbázisból ID alapján.
    """
    # 1. Megkeressük a terméket az ID alapján
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    # 2. Ha nem létezik, 404-es hibát dobunk
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A megadott azonosítójú termék nem található."
        )

    # 3. Töröljük a terméket és elmentjük a változást
    await db.delete(product)
    await db.commit()

    return None