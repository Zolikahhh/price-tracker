import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, Numeric, Boolean, DateTime, ForeignKey, Index, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    subscriptions: Mapped[list["ProductSubscription"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    merchant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    is_in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="product", 
        cascade="all, delete-orphan"
    )

    subscriptions: Mapped[list["ProductSubscription"]] = relationship(
        back_populates="product", 
        cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    product: Mapped["Product"] = relationship(
        back_populates="price_history"
    )

    __table_args__ = (
        Index("idx_price_history_product_time", "product_id", "recorded_at"),
    )


class ProductSubscription(Base):
    __tablename__ = "product_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    target_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    notify_on_stock_change: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(
        back_populates="subscriptions"
    )
    product: Mapped["Product"] = relationship(
        back_populates="subscriptions"
    )