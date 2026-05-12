from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InventoryCount, InventorySession, Product, VarianceReport
from app.services.variance_engine import VarianceEngine

router = APIRouter()


class SessionCreate(BaseModel):
    venue_id: UUID
    session_date: date
    user_id: Optional[UUID] = None
    notes: Optional[str] = None


class CountEntry(BaseModel):
    product_id: UUID
    count_750ml: float = 0
    count_1L: float = 0
    count_1_75L: float = 0
    count_draft_tenths: float = 0
    notes: Optional[str] = None


@router.post("/sessions")
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    session = InventorySession(
        venue_id=payload.venue_id,
        user_id=payload.user_id,
        session_date=payload.session_date,
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{venue_id}")
def list_sessions(venue_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(InventorySession)
        .filter(InventorySession.venue_id == venue_id)
        .order_by(InventorySession.session_date.desc())
        .all()
    )


@router.get("/sessions/{session_id}/counts")
def get_session_counts(session_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(InventoryCount)
        .join(Product, Product.id == InventoryCount.product_id)
        .filter(InventoryCount.session_id == session_id)
        .order_by(Product.name.asc())
        .all()
    )


@router.post("/sessions/{session_id}/counts/bulk")
def save_bulk_counts(session_id: UUID, entries: List[CountEntry], db: Session = Depends(get_db)):
    session = db.query(InventorySession).filter(InventorySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    for entry in entries:
        product = db.query(Product).filter(Product.id == entry.product_id).first()
        if not product:
            continue

        total_ml = (
            (entry.count_750ml * 750)
            + (entry.count_1L * 1000)
            + (entry.count_1_75L * 1750)
            + (entry.count_draft_tenths * float(product.keg_size_ml or 0) / 10)
        )
        bottle_size = float(product.bottle_size_ml or product.keg_size_ml or 1)
        total_value = total_ml * (float(product.bottle_cost or 0) / bottle_size if bottle_size else 0)

        existing = (
            db.query(InventoryCount)
            .filter(InventoryCount.session_id == session_id, InventoryCount.product_id == entry.product_id)
            .first()
        )

        if existing:
            existing.count_750ml = entry.count_750ml
            existing.count_1L = entry.count_1L
            existing.count_1_75L = entry.count_1_75L
            existing.count_draft_tenths = entry.count_draft_tenths
            existing.total_ml = total_ml
            existing.total_value = total_value
            existing.notes = entry.notes
        else:
            db.add(InventoryCount(
                session_id=session_id,
                product_id=entry.product_id,
                count_750ml=entry.count_750ml,
                count_1L=entry.count_1L,
                count_1_75L=entry.count_1_75L,
                count_draft_tenths=entry.count_draft_tenths,
                total_ml=total_ml,
                total_value=total_value,
                notes=entry.notes,
            ))

    db.commit()
    return {"status": "success", "saved": len(entries)}


@router.post("/sessions/{session_id}/calculate")
def calculate_variance(session_id: UUID, db: Session = Depends(get_db)):
    engine = VarianceEngine(db=db, session_id=session_id)
    return engine.calculate()


@router.get("/sessions/{session_id}/variance")
def get_variance_report(session_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(VarianceReport)
        .filter(VarianceReport.session_id == session_id)
        .order_by(VarianceReport.variance_value.desc())
        .all()
    )
