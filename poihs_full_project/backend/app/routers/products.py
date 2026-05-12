from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product

router = APIRouter()


@router.get("/")
def list_products(venue_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(Product)
        .filter(Product.venue_id == venue_id, Product.is_active.is_(True))
        .order_by(Product.name.asc())
        .all()
    )
