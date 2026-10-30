"""Rebuild dashboard/data.js from the star-schema CSVs."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "dashboard" / "data.js"


def load(name: str) -> list[dict[str, str]]:
    with open(DATA / name, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    products = {row["product_id"]: row for row in load("dim_products.csv")}
    regions = {row["region_id"]: row for row in load("dim_regions.csv")}
    orders = load("fact_orders.csv")

    categories = sorted({row["category"] for row in products.values()})
    region_names = sorted({row["region"] for row in regions.values()})
    product_names = sorted({row["product_name"] for row in products.values()})
    cat_index = {name: i for i, name in enumerate(categories)}
    reg_index = {name: i for i, name in enumerate(region_names)}
    prod_index = {name: i for i, name in enumerate(product_names)}

    rows: list[list[object]] = []
    skipped = 0
    for order in orders:
        date = order["order_date"]
        if not date or len(date) < 7 or int(order.get("is_return") or 0):
            skipped += 1
            continue
        product = products[order["product_id"]]
        region = regions[order["region_id"]]
        rows.append(
            [
                int(date[:4]),
                int(date[5:7]),
                reg_index[region["region"]],
                cat_index[product["category"]],
                prod_index[product["product_name"]],
                order["customer_id"],
                round(float(order["sales_amount"]), 2),
                round(float(order["profit"]), 2),
            ]
        )

    payload = {
        "categories": categories,
        "regions": region_names,
        "products": product_names,
        "rows": rows,
        "meta": {
            "source": "fact_orders + dim_products + dim_regions",
            "excluded": skipped,
            "included": len(rows),
            "note": "Returns and orders with invalid dates excluded",
        },
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "window.DASHBOARD_DATA = " + json.dumps(payload, separators=(",", ":")) + ";",
        encoding="utf-8",
    )
    print(f"Wrote {OUT} ({len(rows)} rows, {skipped} skipped)")


if __name__ == "__main__":
    main()
