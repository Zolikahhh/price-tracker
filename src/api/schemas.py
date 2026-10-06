import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, HttpUrl, Field


# ==========================================
# USER SCHEMAS
# ==========================================

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="A jelszónak legalább 8 karakteresnek kell lennie")

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy modellt automatikusan átalakít Pydantic sémává


# ==========================================
# PRODUCT SCHEMAS
# ==========================================

class ProductBase(BaseModel):
    title: str
    url: HttpUrl
    merchant_name: str

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: uuid.UUID
    current_price: Optional[float] = None
    is_in_stock: bool
    last_scraped_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# PRICE HISTORY SCHEMAS
# ==========================================

class PriceHistoryResponse(BaseModel):
    id: int
    product_id: uuid.UUID
    price: float
    is_in_stock: bool
    recorded_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# SUBSCRIPTION SCHEMAS
# ==========================================

class SubscriptionCreate(BaseModel):
    product_id: uuid.UUID
    target_price: Optional[float] = Field(None, gt=0, description="Célár, aminél értesítést kér a user")
    notify_on_stock_change: bool = True

class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    target_price: Optional[float] = None
    notify_on_stock_change: bool
    created_at: datetime

    class Config:
        from_attributes = True