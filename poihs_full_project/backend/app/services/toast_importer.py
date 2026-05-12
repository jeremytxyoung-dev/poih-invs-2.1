import csv
import io
import re
from difflib import get_close_matches
from typing import Any

from app.models import POSImport, POSModifier, POSSale, Product, Recipe


class ToastImporter:
    MODIFIER_RULES = {
        "rocks": 22.5,
        "big rock": 22.5,
        "martini": 40.0,
        "dbl": 37.0,
        "double": 37.0,
        "pint": 37.0,
        "tall": 37.0,
        "shot": 37.0,
        "2 shots": 74.0,
        "rocks glass": 22.5,
        "large": 22.5,
        "old fashioned": 22.5,
    }

    def __init__(self, db):
        self.db = db

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        return re.sub(r"[^a-z0-9]+", " ", text).strip()

    def _default_pour_for_product(self, product: Product) -> float:
        product_type = (product.type or "").lower()
        if product_type == "draft":
            return 473.0
        if product_type == "beer":
            return 370.0
        return float(product.standard_pour_ml or 37.0)

    def _match_recipe_or_product(self, item_name: str) -> tuple[str | None, Any | None]:
        normalized = self.normalize(item_name)
        recipes = self.db.query(Recipe).filter(Recipe.is_active.is_(True)).all()
        products = self.db.query(Product).filter(Product.is_active.is_(True)).all()

        recipe_map = {self.normalize(r.name): r for r in recipes}
        product_map = {self.normalize(p.name): p for p in products}

        if normalized in recipe_map:
            return "recipe", recipe_map[normalized]
        if normalized in product_map:
            return "product", product_map[normalized]

        recipe_match = get_close_matches(normalized, list(recipe_map.keys()), n=1, cutoff=0.8)
        if recipe_match:
            return "recipe", recipe_map[recipe_match[0]]

        product_match = get_close_matches(normalized, list(product_map.keys()), n=1, cutoff=0.8)
        if product_match:
            return "product", product_map[product_match[0]]

        return None, None

    def _recipe_total_ml(self, recipe: Recipe) -> float:
        return float(sum(float(i.amount_ml or 0) for i in recipe.ingredients))

    def _parse_csv(self, file_bytes: bytes) -> list[dict[str, str]]:
        text_stream = io.StringIO(file_bytes.decode("utf-8-sig"))
        reader = csv.DictReader(text_stream)
        return list(reader)

    async def process_product_mix(self, upload_file, venue_id, date_from=None, date_to=None, user_id=None):
        file_bytes = await upload_file.read()
        rows = self._parse_csv(file_bytes)

        pos_import = POSImport(
            venue_id=venue_id,
            user_id=user_id,
            import_type="product_mix",
            file_name=upload_file.filename,
            date_from=date_from,
            date_to=date_to,
            status="processed",
        )
        self.db.add(pos_import)
        self.db.flush()

        matched = 0
        unmatched = 0

        for row in rows:
            item_name = (row.get("Item") or "").strip()
            avg_price = float(row.get("Avg. price") or 0)
            net_sales = float(row.get("Net sales") or 0)
            quantity = float(row.get("Item qty incl. voids") or 0)
            match_type, match_obj = self._match_recipe_or_product(item_name)
            theoretical_ml = 0.0

            if match_type == "recipe":
                theoretical_ml = self._recipe_total_ml(match_obj) * quantity
                matched += 1
            elif match_type == "product":
                theoretical_ml = self._default_pour_for_product(match_obj) * quantity
                matched += 1
            else:
                unmatched += 1

            sale = POSSale(
                pos_import_id=pos_import.id,
                venue_id=venue_id,
                menu_item_name=item_name,
                avg_price=avg_price,
                net_amount=net_sales,
                quantity=quantity,
                theoretical_ml=theoretical_ml,
                sale_date=date_to,
            )
            self.db.add(sale)

        pos_import.records_processed = len(rows)
        pos_import.records_matched = matched
        self.db.commit()

        return {
            "import_id": str(pos_import.id),
            "total_processed": len(rows),
            "matched": matched,
            "unmatched": unmatched,
            "status": "processed",
        }

    async def process_modifiers(self, upload_file, venue_id, date_from=None, date_to=None, user_id=None):
        file_bytes = await upload_file.read()
        rows = self._parse_csv(file_bytes)

        pos_import = POSImport(
            venue_id=venue_id,
            user_id=user_id,
            import_type="modifiers",
            file_name=upload_file.filename,
            date_from=date_from,
            date_to=date_to,
            status="processed",
        )
        self.db.add(pos_import)
        self.db.flush()

        matched = 0

        for row in rows:
            modifier_name = (row.get("Modifier") or "").strip()
            parent_item = (row.get("Parent Menu Selection") or "").strip()
            quantity = float(row.get("Qty") or 0)
            normalized = self.normalize(modifier_name)
            extra_ml = 0.0

            for key, value in self.MODIFIER_RULES.items():
                if key in normalized:
                    extra_ml = value * quantity
                    matched += 1
                    break

            modifier = POSModifier(
                pos_import_id=pos_import.id,
                venue_id=venue_id,
                modifier_name=modifier_name,
                parent_menu_item=parent_item,
                quantity=quantity,
                extra_ml=extra_ml,
                sale_date=date_to,
            )
            self.db.add(modifier)

        pos_import.records_processed = len(rows)
        pos_import.records_matched = matched
        self.db.commit()

        return {
            "import_id": str(pos_import.id),
            "total_processed": len(rows),
            "matched": matched,
            "unmatched": len(rows) - matched,
            "status": "processed",
        }
