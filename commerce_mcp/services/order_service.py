from commerce_mcp.repositories.order_repository import OrderRepository


class OrderService:

    def __init__(self, repository: OrderRepository | None = None):
        self.repository = (
            repository
            if repository is not None
            else OrderRepository()
        )

    def check_order_status(
        self,
        customer_id: int,
        order_number: int,
    ) -> dict:

        result = self.repository.get_order_status(
            customer_id=customer_id,
            order_number=order_number,
        )

        if result is None:
            return {
                "success": False,
                "code": "ORDER_NOT_FOUND_OR_NOT_ACCESSIBLE",
                "message": "Order was not found or is not accessible.",
            }

        return {
            "success": True,
            "code": "ORDER_STATUS_FOUND",
            "data": result,
        }

    def list_customer_orders(
        self,
        customer_id: int,
        limit: int = 10,
    ) -> dict:

        orders = self.repository.list_customer_orders(
            customer_id=customer_id,
            limit=limit,
        )

        return {
            "success": True,
            "code": "CUSTOMER_ORDERS_FOUND",
            "count": len(orders),
            "data": orders,
        }

    def place_order(
        self,
        customer_id: int,
        product_id: int,
        quantity: int,
        address_id: int,
        idempotency_key: str,
    ) -> dict:

        if quantity <= 0:
            return {
                "success": False,
                "code": "INVALID_QUANTITY",
                "message": "Quantity must be greater than zero.",
            }

        if not idempotency_key.strip():
            return {
                "success": False,
                "code": "INVALID_IDEMPOTENCY_KEY",
                "message": "Idempotency key is required.",
            }

        result = self.repository.place_order(
            customer_id=customer_id,
            product_id=product_id,
            quantity=quantity,
            address_id=address_id,
            idempotency_key=idempotency_key,
        )

        status = result["status"]

        if status == "ORDER_PLACED":
            return {
                "success": True,
                "code": "ORDER_PLACED",
                "data": result,
            }

        if status == "ALREADY_PROCESSED":
            return {
                "success": True,
                "code": "ORDER_ALREADY_PROCESSED",
                "data": result["order"],
            }

        if status == "INSUFFICIENT_STOCK":
            return {
                "success": False,
                "code": "INSUFFICIENT_STOCK",
                "available_stock": result["available_stock"],
            }

        return {
            "success": False,
            "code": status,
        }