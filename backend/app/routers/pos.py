from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import POSImport
from app.services.toast_importer import ToastImporter

router = APIRouter()


@router.post("/import/product-mix")
async def import_product_mix(
    venue_id: UUID = Form(...),
    date_from: Optional[date] = Form(None),
    date_to: Optional[date] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    importer = ToastImporter(db)
    return await importer.process_product_mix(file, venue_id, date_from=date_from, date_to=date_to)


@router.post("/import/modifiers")
async def import_modifiers(
    venue_id: UUID = Form(...),
    date_from: Optional[date] = Form(None),
    date_to: Optional[date] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    importer = ToastImporter(db)
    return await importer.process_modifiers(file, venue_id, date_from=date_from, date_to=date_to)


@router.get("/imports/{venue_id}")
def list_imports(venue_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(POSImport)
        .filter(POSImport.venue_id == venue_id)
        .order_by(POSImport.created_at.desc())
        .all()
    )
