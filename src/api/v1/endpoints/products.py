import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.schemas import ProductCreate, ProductResponse
from src.db.models import Product

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Új termék felvétele az adatbázisba.
    """
    # Ellenőrizzük, hogy létezik-e már a termék a megadott URL alapján
    query = select(Product).where(Product.url == str(product_in.url))
    result = await db.execute(query)
    existing_product = result.scalar_one_or_none()

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ez a termék URL már szerepel az adatbázisban."
        )

    # Új Product ORM objektum létrehozása
    db_product = Product(
        title=product_in.title,
        url=str(product_in.url),
        merchant_name=product_in.merchant_name
    )

    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Az összes regisztrált termék kilistázása (lapozással).
    """
    query = select(Product).offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Egy konkrét termék lekérése ID alapján.
    """
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A megadott termék nem található."
        )

    return product