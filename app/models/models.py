from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy import String, Numeric, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash

from app.models.base import db


class AdminUser(db.Model):
    __tablename__ = "admin_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class UnitStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
    DEFECT = "DEFECT"
    RETURNED = "RETURNED"

class CostSource(str, Enum):
    MANUAL = "manual"
    ALLOCATED = "allocated"

class CostType(str, Enum):
    FREIGHT_INTL = "freight_intl"
    FREIGHT_BR = "freight_br"
    INSURANCE = "insurance"
    CARD_FEE = "card_fee"
    IMPORT_TAX = "import_tax"
    BROKER_FEE = "broker_fee"
    INVOICE_TAX = "invoice_tax"
    OTHER = "other"


class ProductModel(db.Model):
    __tablename__ = "product_model"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_gb: Mapped[Optional[int]] = mapped_column()
    variant: Mapped[Optional[str]] = mapped_column(String(100))
    
    units: Mapped[List["Unit"]] = relationship(back_populates="product_model")


class PurchaseLot(db.Model):
    __tablename__ = "purchase_lot"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    supplier: Mapped[str] = mapped_column(String(200), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column()

    units: Mapped[List["Unit"]] = relationship(back_populates="purchase_lot")


class Unit(db.Model):
    __tablename__ = "unit"

    id: Mapped[int] = mapped_column(primary_key=True)
    serial: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    product_model_id: Mapped[int] = mapped_column(ForeignKey("product_model.id", ondelete="RESTRICT"), nullable=False)
    purchase_lot_id: Mapped[int] = mapped_column(ForeignKey("purchase_lot.id", ondelete="RESTRICT"), nullable=False)
    usd_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[UnitStatus] = mapped_column(SAEnum(UnitStatus), default=UnitStatus.AVAILABLE, nullable=False)
    holder: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    product_model: Mapped["ProductModel"] = relationship(back_populates="units")
    purchase_lot: Mapped["PurchaseLot"] = relationship(back_populates="units")
    costs: Mapped[List["UnitCost"]] = relationship(back_populates="unit", cascade="all, delete-orphan")
    sale: Mapped[Optional["Sale"]] = relationship(back_populates="unit", uselist=False)

class UnitCost(db.Model):
    __tablename__ = "unit_cost"

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("unit.id", ondelete="RESTRICT"), nullable=False)
    cost_type: Mapped[CostType] = mapped_column(SAEnum(CostType), nullable=False)
    brl_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    source: Mapped[CostSource] = mapped_column(SAEnum(CostSource), nullable=False)
    lot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_lot.id", ondelete="RESTRICT"))
    allocation_run_id: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    unit: Mapped["Unit"] = relationship(back_populates="costs")


class Sale(db.Model):
    __tablename__ = "sale"

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("unit.id", ondelete="RESTRICT"), unique=True, nullable=False)
    sold_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    sell_price_brl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    commission_brl: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    channel: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column()

    unit: Mapped["Unit"] = relationship(back_populates="sale")
