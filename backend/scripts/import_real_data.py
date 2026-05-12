import argparse
import csv
from datetime import datetime
from difflib import get_close_matches

from sqlalchemy import create_engine, text

RECIPE_ML_MAP = {
    "green tea": 22.5,
    "lemon drop": 22.5,
    "mexican candy": 37.5,
    "vegas bomb": 45,
    "star fucker": 30,
    "margarita": 45,
    "ranch water": 45,
    "paloma": 45,
    "ice house mule": 45,
    "po old fashioned": 60,
    "aperol spritz": 60,
    "lit": 60,
    "white tea": 30,
    "espresso martini": 30,
    "lemon drop martini": 45,
    "strawberry fields": 60,
    "lychee martini": 60,
    "k-pop mule": 60,
    "post oak spritz": 60,
}

MODIFIER_RULES = {
    "rocks": 22.5,
    "big rock": 22.5,
    "martini": 40,
    "dbl": 37,
    "double": 37,
    "pint": 37,
    "tall": 37,
    "shot": 37,
    "2 shots": 74,
    "rocks glass": 22.5,
    "large": 22.5,
    "old fashioned": 22.5,
}


def normalize(value: str) -> str:
    return (value or "").strip().lower()


def match_recipe_ml(name: str) -> float:
    normalized = normalize(name)
    if normalized in RECIPE_ML_MAP:
        return RECIPE_ML_MAP[normalized]
    match = get_close_matches(normalized, RECIPE_ML_MAP.keys(), n=1, cutoff=0.8)
    return RECIPE_ML_MAP[match[0]] if match else 0


def import_product_mix(conn, venue_id, csv_path, sale_date):
    processed = matched = unmatched = 0
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_name = row.get("Item", "")
            avg_price = float(row.get("Avg. price") or 0)
            net_sales = float(row.get("Net sales") or 0)
            quantity = float(row.get("Item qty incl. voids") or 0)
            theoretical_ml = match_recipe_ml(item_name)
            if theoretical_ml:
                theoretical_ml *= quantity
                matched += 1
            else:
                item_lower = normalize(item_name)
                if "draft" in item_lower:
                    theoretical_ml = 473 * quantity
                elif "beer" in item_lower or "btl" in item_lower or "bottle" in item_lower:
                    theoretical_ml = 370 * quantity
                else:
                    theoretical_ml = 37 * quantity
                unmatched += 1
            conn.execute(text("""
                INSERT INTO pos_sales (id, pos_import_id, venue_id, menu_item_name, avg_price, net_amount, quantity, theoretical_ml, sale_date, created_at, updated_at)
                VALUES (gen_random_uuid(), gen_random_uuid(), :venue_id, :menu_item_name, :avg_price, :net_amount, :quantity, :theoretical_ml, :sale_date, NOW(), NOW())
            """), {
                "venue_id": venue_id,
                "menu_item_name": item_name,
                "avg_price": avg_price,
                "net_amount": net_sales,
                "quantity": quantity,
                "theoretical_ml": theoretical_ml,
                "sale_date": sale_date,
            })
            processed += 1
    return processed, matched, unmatched


def import_modifiers(conn, venue_id, csv_path, sale_date):
    processed = matched = unmatched = 0
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            modifier_name = row.get("Modifier", "")
            parent_item = row.get("Parent Menu Selection", "")
            quantity = float(row.get("Qty") or 0)
            extra_ml = 0
            normalized = normalize(modifier_name)
            for key, value in MODIFIER_RULES.items():
                if key in normalized:
                    extra_ml = value * quantity
                    matched += 1
                    break
            if not extra_ml:
                unmatched += 1
            conn.execute(text("""
                INSERT INTO pos_modifiers (id, pos_import_id, venue_id, modifier_name, parent_menu_item, quantity, extra_ml, sale_date, created_at, updated_at)
                VALUES (gen_random_uuid(), gen_random_uuid(), :venue_id, :modifier_name, :parent_menu_item, :quantity, :extra_ml, :sale_date, NOW(), NOW())
            """), {
                "venue_id": venue_id,
                "modifier_name": modifier_name,
                "parent_menu_item": parent_item,
                "quantity": quantity,
                "extra_ml": extra_ml,
                "sale_date": sale_date,
            })
            processed += 1
    return processed, matched, unmatched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--venue-id", required=True)
    parser.add_argument("--product-mix")
    parser.add_argument("--modifiers")
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    sale_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    engine = create_engine(args.db_url)

    with engine.begin() as conn:
        total_processed = total_matched = total_unmatched = 0
        if args.product_mix:
            p, m, u = import_product_mix(conn, args.venue_id, args.product_mix, sale_date)
            total_processed += p
            total_matched += m
            total_unmatched += u
        if args.modifiers:
            p, m, u = import_modifiers(conn, args.venue_id, args.modifiers, sale_date)
            total_processed += p
            total_matched += m
            total_unmatched += u

    print(f"Processed: {total_processed}")
    print(f"Matched: {total_matched}")
    print(f"Unmatched: {total_unmatched}")


if __name__ == "__main__":
    main()
