from commerce_mcp.repositories.warranty_repository import (
    WarrantyRepository,
)


class WarrantyService:

    def __init__(
        self,
        repository: WarrantyRepository | None = None,
    ):
        self.repository = (
            repository
            if repository is not None
            else WarrantyRepository()
        )

    def get_warranty_details(
        self,
        customer_id: int,
        order_number: str,
        product_id: int,
    ) -> dict:

        result = self.repository.get_warranty_details(
            customer_id=customer_id,
            order_number=order_number,
            product_id=product_id,
        )

        if result is None:
            return {
                "success": False,
                "code": "ORDER_ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE",
                "message": (
                    "The requested product was not found "
                    "in this customer's order."
                ),
            }

        if result["warranty_plan_id"] is None:
            return {
                "success": True,
                "code": "NO_EXTENDED_WARRANTY",
                "data": {
                    "order_number": result["order_number"],
                    "product_id": result["product_id"],
                    "product_name": result["product_name"],
                    "has_extended_warranty": False,
                },
            }

        return {
            "success": True,
            "code": "WARRANTY_FOUND",
            "data": {
                **result,
                "has_extended_warranty": True,
            },
        }