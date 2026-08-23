from commerce_mcp.repositories.product_repository import (
    ProductRepository,
)


class ProductService:

    def __init__(
        self,
        repository: ProductRepository | None = None,
    ):
        self.repository = (
            repository
            if repository is not None
            else ProductRepository()
        )

    def get_product_details(
        self,
        product_id: int,
    ) -> dict:

        product = self.repository.get_product_details(
            product_id
        )

        if product is None:
            return {
                "success": False,
                "code": "PRODUCT_NOT_FOUND",
                "message": "Product was not found.",
            }

        return {
            "success": True,
            "code": "PRODUCT_FOUND",
            "data": product,
        }

    def search_products(self, **kwargs) -> dict:

        products = self.repository.search_products(
            **kwargs
        )

        return {
            "success": True,
            "code": "PRODUCTS_FOUND",
            "count": len(products),
            "data": products,
        }