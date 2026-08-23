from sqlalchemy import text

from commerce_mcp.db import engine


class WarrantyRepository:

    def get_warranty_details(
        self,
        customer_id: int,
        order_number: str,
        product_id: int,
    ) -> dict | None:

        sql = text("""
            SELECT
                o.order_number,
                oi.order_item_id,
                p.product_id,
                p.sku,
                p.name AS product_name,

                wp.warranty_plan_id,
                wp.name AS warranty_plan_name,
                wp.duration_months,

                cw.purchase_price,
                cw.valid_from,
                cw.valid_until,
                cw.status

            FROM orders o

            JOIN order_items oi
                ON oi.order_id = o.order_id

            JOIN products p
                ON p.product_id = oi.product_id

            LEFT JOIN customer_warranties cw
                ON cw.order_item_id = oi.order_item_id

            LEFT JOIN warranty_plans wp
                ON wp.warranty_plan_id = cw.warranty_plan_id

            WHERE o.customer_id = :customer_id
              AND o.order_number = :order_number
              AND p.product_id = :product_id
        """)

        with engine.connect() as connection:
            row = connection.execute(
                sql,
                {
                    "customer_id": customer_id,
                    "order_number": order_number,
                    "product_id": product_id,
                },
            ).mappings().first()

            return dict(row) if row else None