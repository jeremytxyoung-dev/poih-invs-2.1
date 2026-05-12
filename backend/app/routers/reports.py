from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, InventorySession, POSImport, POSSale, Product, VarianceReport

router = APIRouter()


@router.get("/dashboard/{venue_id}")
def dashboard(venue_id: UUID, db: Session = Depends(get_db)):
    latest_session = (
        db.query(InventorySession)
        .filter(InventorySession.venue_id == venue_id)
        .order_by(InventorySession.session_date.desc())
        .first()
    )

    top_movers = (
        db.query(
            POSSale.menu_item_name,
            func.sum(POSSale.quantity).label("qty"),
            func.sum(POSSale.net_amount).label("revenue"),
        )
        .filter(POSSale.venue_id == venue_id)
        .group_by(POSSale.menu_item_name)
        .order_by(func.sum(POSSale.quantity).desc())
        .limit(5)
        .all()
    )

    hotspots = []
    flagged_count = 0
    latest_variance = 0
    if latest_session:
        hotspot_rows = (
            db.query(VarianceReport, Product, Category)
            .join(Product, Product.id == VarianceReport.product_id)
            .join(Category, Category.id == Product.category_id)
            .filter(VarianceReport.session_id == latest_session.id)
            .filter(VarianceReport.variance_value < 0)
            .order_by(VarianceReport.variance_value.asc())
            .limit(5)
            .all()
        )
        hotspots = [
            {
                "name": product.name,
                "category": category.name,
                "loss_amount": float(report.variance_value),
            }
            for report, product, category in hotspot_rows
        ]
        flagged_count = db.query(func.count(VarianceReport.id)).filter(VarianceReport.session_id == latest_session.id, VarianceReport.is_flagged.is_(True)).scalar() or 0
        latest_variance = float(latest_session.total_variance_value or 0)

    return {
        "latest_session_date": str(latest_session.session_date) if latest_session else None,
        "latest_variance": latest_variance,
        "flagged_count": flagged_count,
        "top_movers": [
            {"name": row.menu_item_name, "qty": float(row.qty or 0), "revenue": float(row.revenue or 0)}
            for row in top_movers
        ],
        "shrinkage_hotspots": hotspots,
    }


@router.get("/variance-trend/{venue_id}")
def variance_trend(venue_id: UUID, weeks: int = 8, db: Session = Depends(get_db)):
    rows = (
        db.query(
            InventorySession.session_date,
            func.sum(VarianceReport.variance_value).label("variance_value"),
            func.avg(VarianceReport.accuracy_pct).label("accuracy"),
        )
        .join(VarianceReport, VarianceReport.session_id == InventorySession.id)
        .filter(InventorySession.venue_id == venue_id)
        .group_by(InventorySession.session_date)
        .order_by(InventorySession.session_date.desc())
        .limit(weeks)
        .all()
    )
    return [
        {
            "date": str(row.session_date),
            "variance_value": float(row.variance_value or 0),
            "accuracy": float(row.accuracy or 0),
        }
        for row in rows
    ]


@router.get("/category-performance/{venue_id}")
def category_performance(venue_id: UUID, db: Session = Depends(get_db)):
    rows = (
        db.query(
            Category.name.label("category"),
            func.count(Product.id).label("product_count"),
            func.sum(VarianceReport.variance_value).label("total_variance"),
            func.avg(VarianceReport.accuracy_pct).label("avg_accuracy"),
        )
        .join(Product, Product.category_id == Category.id)
        .outerjoin(VarianceReport, VarianceReport.product_id == Product.id)
        .filter(Category.venue_id == venue_id)
        .group_by(Category.name)
        .order_by(Category.name.asc())
        .all()
    )
    return [
        {
            "category": row.category,
            "product_count": int(row.product_count or 0),
            "total_variance": float(row.total_variance or 0),
            "avg_accuracy": float(row.avg_accuracy or 0),
        }
        for row in rows
    ]
