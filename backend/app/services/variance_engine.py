from sqlalchemy import func

from app.models import Adjustment, InventoryCount, InventorySession, POSImport, POSModifier, POSSale, Product, Purchase, VarianceReport


class VarianceEngine:
    def __init__(self, db, session_id):
        self.db = db
        self.session_id = session_id

    def calculate(self):
        session = self.db.query(InventorySession).filter(InventorySession.id == self.session_id).first()
        if not session:
            raise ValueError("Inventory session not found")

        counts = (
            self.db.query(InventoryCount)
            .join(Product, Product.id == InventoryCount.product_id)
            .filter(InventoryCount.session_id == self.session_id)
            .all()
        )

        reports = []
        total_variance_value = 0.0
        flagged_count = 0

        self.db.query(VarianceReport).filter(VarianceReport.session_id == self.session_id).delete()
        self.db.flush()

        for count in counts:
            product = count.product
            current_ml = float(count.total_ml or 0)
            previous_ml = float(count.previous_total_ml or 0)

            purchases_ml = float(
                self.db.query(func.coalesce(func.sum(Purchase.received_ml), 0))
                .join(Product, Product.id == Purchase.product_id)
                .filter(Purchase.product_id == product.id)
                .scalar()
                or 0
            )

            usage_sales_ml = float(
                self.db.query(func.coalesce(func.sum(POSSale.theoretical_ml), 0))
                .join(POSImport, POSImport.id == POSSale.pos_import_id)
                .filter(POSSale.venue_id == session.venue_id)
                .filter(POSSale.sale_date == session.session_date)
                .scalar()
                or 0
            )

            usage_modifiers_ml = float(
                self.db.query(func.coalesce(func.sum(POSModifier.extra_ml), 0))
                .join(POSImport, POSImport.id == POSModifier.pos_import_id)
                .filter(POSModifier.venue_id == session.venue_id)
                .filter(POSModifier.sale_date == session.session_date)
                .scalar()
                or 0
            )

            adjustments_ml = float(
                self.db.query(func.coalesce(func.sum(Adjustment.amount_ml), 0))
                .filter(Adjustment.session_id == self.session_id, Adjustment.product_id == product.id)
                .scalar()
                or 0
            )

            usage_ml = usage_sales_ml + usage_modifiers_ml
            variance_ml = current_ml - ((previous_ml + purchases_ml) - usage_ml) + adjustments_ml

            bottle_size = float(product.bottle_size_ml or product.keg_size_ml or 1)
            cost_per_ml = float(product.bottle_cost or 0) / bottle_size if bottle_size else 0
            variance_value = variance_ml * cost_per_ml
            expected_inventory = max((previous_ml + purchases_ml) - usage_ml, 1)
            accuracy_pct = (current_ml / expected_inventory) * 100

            is_flagged = False
            flag_reason = None
            product_type = (product.type or "").lower()

            if product_type == "spirit" and (abs(variance_value) > 20 or accuracy_pct < 90):
                is_flagged = True
                flag_reason = "Spirit threshold exceeded"
            elif product_type == "beer" and (abs(variance_value) > 15 or accuracy_pct < 85):
                is_flagged = True
                flag_reason = "Beer threshold exceeded"
            elif product_type == "draft" and abs(variance_ml) > 10000:
                is_flagged = True
                flag_reason = "Draft variance threshold exceeded"

            report = VarianceReport(
                session_id=self.session_id,
                product_id=product.id,
                current_ml=current_ml,
                previous_ml=previous_ml,
                purchases_ml=purchases_ml,
                theoretical_usage_ml=usage_ml,
                adjustments_ml=adjustments_ml,
                variance_ml=variance_ml,
                variance_value=variance_value,
                accuracy_pct=accuracy_pct,
                is_flagged=is_flagged,
                flag_reason=flag_reason,
            )
            self.db.add(report)

            reports.append({
                "product_id": str(product.id),
                "product_name": product.name,
                "variance_ml": round(variance_ml, 2),
                "variance_value": round(variance_value, 2),
                "accuracy_pct": round(accuracy_pct, 2),
                "is_flagged": is_flagged,
                "flag_reason": flag_reason,
            })

            total_variance_value += variance_value
            if is_flagged:
                flagged_count += 1

        session.total_variance_value = round(total_variance_value, 2)
        self.db.commit()

        return {
            "session_id": str(session.id),
            "total_variance": round(total_variance_value, 2),
            "flagged_count": flagged_count,
            "products": reports,
        }
