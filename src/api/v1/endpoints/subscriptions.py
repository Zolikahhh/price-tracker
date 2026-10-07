import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_current_user
from src.api.schemas import SubscriptionCreate, SubscriptionResponse
from src.db.models import ProductSubscription, Product, User

router = APIRouter()


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    sub_in: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Termékfigyelésre való feliratkozás (védett végpont).
    """
    # 1. Ellenőrizzük, hogy létezik-e a termék
    product_query = select(Product).where(Product.id == sub_in.product_id)
    product_res = await db.execute(product_query)
    if not product_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A megadott termék nem található."
        )

    # 2. Ellenőrizzük, hogy fel van-e már iratkozva erre a termékre a user
    sub_query = select(ProductSubscription).where(
        ProductSubscription.user_id == current_user.id,
        ProductSubscription.product_id == sub_in.product_id
    )
    sub_res = await db.execute(sub_query)
    if sub_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Már feliratkoztál erre a termékre."
        )

    # 3. Feliratkozás mentése
    db_sub = ProductSubscription(
        user_id=current_user.id,
        product_id=sub_in.product_id,
        target_price=sub_in.target_price,
        notify_on_stock_change=sub_in.notify_on_stock_change
    )
    db.add(db_sub)
    await db.commit()
    await db.refresh(db_sub)

    return db_sub


@router.get("/me", response_model=List[SubscriptionResponse])
async def get_my_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    A bejelentkezett felhasználó saját feliratkozásainak kilistázása.
    """
    query = select(ProductSubscription).where(ProductSubscription.user_id == current_user.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Feliratkozás törlése ID alapján.
    """
    query = select(ProductSubscription).where(
        ProductSubscription.id == subscription_id,
        ProductSubscription.user_id == current_user.id
    )
    result = await db.execute(query)
    sub = result.scalar_one_or_none()

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A feliratkozás nem található vagy nem a tiéd."
        )

    await db.delete(sub)
    await db.commit()
    return None