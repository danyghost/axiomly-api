from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Integer,
    func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    valuation_requests: Mapped[List["ValuationRequest"]] = relationship(back_populates="client")


class ValuationRequest(Base):
    __tablename__ = "valuation_requests"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    client: Mapped["Client"] = relationship(back_populates="valuation_requests")
    result: Mapped[Optional["ValuationResult"]] = relationship(back_populates="request", uselist=False)


class ValuationResult(Base):
    __tablename__ = "valuation_results"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("valuation_requests.id", ondelete="CASCADE"), nullable=False, unique=True)

    price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request: Mapped["ValuationRequest"] = relationship(back_populates="result")


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    snapshot: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)