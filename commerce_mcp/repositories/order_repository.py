from sqlalchemy import text

from commerce_mcp.db import engine
import secrets
import json

class OrderRepository:

    def get_order_status(
        self,
        customer_id: int,
        order_number : int,
    ) -> dict | None:

        order_sql = text("""
            SELECT
                o.order_id,
                o.customer_id,
                o.order_status,
                o.total_amount,
                o.currency,
                o.order_date
            FROM orders o
            WHERE o.order_number = :order_number
              AND o.customer_id = :customer_id
        """)

        shipments_sql = text("""
            SELECT
                s.shipment_id,
                s.carrier,
                s.tracking_number,
                s.current_status,
                s.shipping_address,
                s.shipped_at,
                s.estimated_delivery_at,
                s.delivered_at
            FROM shipments s
            WHERE s.order_id = :order_id
            ORDER BY s.shipment_id
        """)

        with engine.connect() as connection:

            order_row = connection.execute(
                order_sql,
                {
                    "order_number": order_number,
                    "customer_id": customer_id,
                },
            ).mappings().first()    

            if order_row is None:
                return None

            internal_order_id = order_row["order_id"]
            shipment_rows = connection.execute(
                shipments_sql,
                {
                    "order_id": internal_order_id,
                },
            ).mappings().all()

            return {
                "order": dict(order_row),
                "shipments": [
                    dict(row)
                    for row in shipment_rows
                ],
            }

    def list_customer_orders(
        self,
        customer_id: int,
        limit: int = 10,
    ) -> list[dict]:

        sql = text("""
            SELECT
                order_number,
                order_status,
                total_amount,
                currency,
                order_date
            FROM orders
            WHERE customer_id = :customer_id
            ORDER BY order_date DESC
            LIMIT :limit
        """)

        with engine.connect() as connection:
            rows = connection.execute(
                sql,
                {
                    "customer_id": customer_id,
                    "limit": min(limit, 50),
                },
            ).mappings().all()

            return [dict(row) for row in rows]

    def place_order(
        self,
        customer_id: int,
        product_id: int,
        quantity: int,
        address_id: int,
        idempotency_key: str,
    ) -> dict:
        with engine.begin() as connection:

            existing_order = connection.execute(
                text("""
                    SELECT
                        order_id,
                        order_number,
                        order_status
                    FROM orders
                    WHERE idempotency_key = :idempotency_key
                """),
                {
                    "idempotency_key": idempotency_key,
                },
            ).mappings().first()

            if existing_order:
                return {
                    "status": "ALREADY_PROCESSED",
                    "order": dict(existing_order),
                }

            customer = connection.execute(
                text("""
                    SELECT customer_id
                    FROM customers
                    WHERE customer_id = :customer_id
                """),
                {
                    "customer_id": customer_id,
                },
            ).mappings().first()

            if customer is None:
                return {
                    "status": "CUSTOMER_NOT_FOUND"
                }

            address = connection.execute(
                text("""
                    SELECT
                        address_id,
                        address_line1,
                        address_line2,
                        city,
                        state,
                        postal_code,
                        country_code
                    FROM customer_addresses
                    WHERE address_id = :address_id
                    AND customer_id = :customer_id
                """),
                {
                    "address_id": address_id,
                    "customer_id": customer_id,
                },
            ).mappings().first()

            if address is None:
                return {
                    "status": "ADDRESS_NOT_FOUND_OR_NOT_ACCESSIBLE"
                }

            product = connection.execute(
                text("""
                    SELECT
                        product_id,
                        name,
                        price,
                        currency,
                        stock_quantity,
                        active
                    FROM products
                    WHERE product_id = :product_id
                    FOR UPDATE
                """),
                {
                    "product_id": product_id,
                },
            ).mappings().first()

            if product is None:
                return {
                    "status": "PRODUCT_NOT_FOUND"
                }

            if not product["active"]:
                return {
                    "status": "PRODUCT_INACTIVE"
                }

            if product["stock_quantity"] < quantity:
                return {
                    "status": "INSUFFICIENT_STOCK",
                    "available_stock": product["stock_quantity"],
                }

            total_amount = product["price"] * quantity
            order_number = generate_order_number()

            order_result = connection.execute(
                text("""
                    INSERT INTO orders (
                        order_number,
                        customer_id,
                        order_status,
                        total_amount,
                        currency,
                        idempotency_key
                    )
                    VALUES (
                        :order_number,
                        :customer_id,
                        'PLACED',
                        :total_amount,
                        :currency,
                        :idempotency_key
                    )
                """),
                {
                    "order_number": order_number,
                    "customer_id": customer_id,
                    "total_amount": total_amount,
                    "currency": product["currency"],
                    "idempotency_key": idempotency_key,
                },
            )

            order_id = order_result.lastrowid
            order_item_result = connection.execute(
                text("""
                    INSERT INTO order_items (
                        order_id,
                        product_id,
                        quantity,
                        unit_price,
                        line_total
                    )
                    VALUES (
                        :order_id,
                        :product_id,
                        :quantity,
                        :unit_price,
                        :line_total
                    )
                """),
                {
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": product["price"],
                    "line_total": total_amount,
                },
            )
            order_item_id = order_item_result.lastrowid

            shipping_address = json.dumps({
                "address_line1": address["address_line1"],
                "address_line2": address["address_line2"],
                "city": address["city"],
                "state": address["state"],
                "postal_code": address["postal_code"],
                "country_code": address["country_code"],
            }) 

            shipment_result = connection.execute(
                text("""
                    INSERT INTO shipments (
                        order_id,
                        current_status,
                        shipping_address
                    )
                    VALUES (
                        :order_id,
                        'CREATED',
                        :shipping_address
                    )
                """),
                {
                    "order_id": order_id,
                    "shipping_address": shipping_address,
                },
            )

            shipment_id = shipment_result.lastrowid

            connection.execute(
                text("""
                    INSERT INTO shipment_items (
                        shipment_id,
                        order_item_id,
                        quantity
                    )
                    VALUES (
                        :shipment_id,
                        :order_item_id,
                        :quantity
                    )
                """),
                {
                    "shipment_id": shipment_id,
                    "order_item_id": order_item_id,
                    "quantity": quantity,
                },
            )                       

            connection.execute(
                text("""
                    UPDATE products
                    SET stock_quantity = stock_quantity - :quantity
                    WHERE product_id = :product_id
                """),
                {
                    "quantity": quantity,
                    "product_id": product_id,
                },
            )

            return {
                "status": "ORDER_PLACED",
                "order_id": order_id,
                "order_number": order_number,
                "total_amount": total_amount,
                "currency": product["currency"],
            }

    def list_customer_addresses(
        self,
        customer_id: int,
    ) -> list[dict]:

        with engine.connect() as connection:
            rows = connection.execute(
                text("""
                    SELECT
                        address_id,
                        address_line1,
                        address_line2,
                        city,
                        state,
                        postal_code,
                        country_code
                    FROM customer_addresses
                    WHERE customer_id = :customer_id
                    ORDER BY address_id
                """),
                {
                    "customer_id": customer_id,
                },
            ).mappings().all()

            return [
                dict(row)
                for row in rows
            ]

    def get_order_details(
        self,
        customer_id: int,
        order_number: str,
    ) -> dict | None:

        order_sql = text("""
            SELECT
                o.order_id,
                o.order_number,
                o.order_status,
                o.total_amount,
                o.currency,
                o.order_date
            FROM orders o
            WHERE o.customer_id = :customer_id
            AND o.order_number = :order_number
        """)

        items_sql = text("""
            SELECT
                oi.order_item_id,
                p.product_id,
                p.sku,
                p.name AS product_name,
                oi.quantity,
                oi.unit_price,
                oi.line_total
            FROM order_items oi
            JOIN products p
                ON p.product_id = oi.product_id
            WHERE oi.order_id = :order_id
            ORDER BY oi.order_item_id
        """)

        with engine.connect() as connection:
            order_row = connection.execute(
                order_sql,
                {
                    "customer_id": customer_id,
                    "order_number": order_number,
                },
            ).mappings().first()

            if order_row is None:
                return None

            item_rows = connection.execute(
                items_sql,
                {
                    "order_id": order_row["order_id"],
                },
            ).mappings().all()

            return {
                "order": dict(order_row),
                "items": [
                    dict(row)
                    for row in item_rows
                ],
            }


def generate_order_number() -> str:
    return f"ORD-{secrets.token_hex(8).upper()}"



if __name__ == "__main__":
    repo = OrderRepository()

    print(repo.get_order_status(
        customer_id=1,
        order_number="ORD-2026-000001",
    ))
