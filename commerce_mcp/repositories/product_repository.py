from sqlalchemy import text

from commerce_mcp.db import engine


class ProductRepository:

    def get_product_details(
        self,
        product_id: int,
    ) -> dict | None:

        sql = text("""
            SELECT
                product_id,
                sku,
                name,
                description,
                category,
                brand,
                price,
                currency,
                stock_quantity,
                active
            FROM products
            WHERE product_id = :product_id
        """)

        with engine.connect() as connection:
            row = connection.execute(
                sql,
                {"product_id": product_id},
            ).mappings().first()

            return dict(row) if row else None


    def search_products(
        self,
        category: str | None = None,
        brand: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock_only: bool = True,
        limit: int = 10,
    ) -> list[dict]:

        conditions = ["active = TRUE"]

        params = {
            "limit": min(limit, 50)
        }

        if category:
            conditions.append("category = :category")
            params["category"] = category

        if brand:
            conditions.append("brand = :brand")
            params["brand"] = brand

        if min_price is not None:
            conditions.append("price >= :min_price")
            params["min_price"] = min_price

        if max_price is not None:
            conditions.append("price <= :max_price")
            params["max_price"] = max_price

        if in_stock_only:
            conditions.append("stock_quantity > 0")

        where_clause = " AND ".join(conditions)

        sql = text(f"""
            SELECT
                product_id,
                sku,
                name,
                category,
                brand,
                price,
                currency,
                stock_quantity
            FROM products
            WHERE {where_clause}
            ORDER BY price
            LIMIT :limit
        """)

        with engine.connect() as connection:
            rows = connection.execute(
                sql,
                params,
            ).mappings().all()

            return [dict(row) for row in rows]