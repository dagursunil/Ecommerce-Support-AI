from mcp.server import MCPServer

from commerce_mcp.services.order_service import OrderService
from commerce_mcp.services.product_service import ProductService
from commerce_mcp.services.warranty_service import WarrantyService
from mcp.server.mcpserver import Context


mcp = MCPServer(
    name="commerce-mcp",
    description="Commerce operations for eCommSupport-AI",
)

order_service = OrderService()
product_service = ProductService()
warranty_service = WarrantyService()


@mcp.tool()
def check_order_status(
    customer_id: int,
    order_number: str,
) -> dict:
    """
    Check the status of a customer's order.
    """

    return order_service.check_order_status(
        customer_id=customer_id,
        order_number=order_number,
    )


@mcp.tool()
def list_customer_orders(
    customer_id: int,
    limit: int = 10,
) -> dict:
    """
    List a customer's most recent orders.
    """

    return order_service.list_customer_orders(
        customer_id=customer_id,
        limit=limit,
    )


@mcp.tool()
def search_products(
    category: str | None = None,
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool = True,
    limit: int = 10,
) -> dict:
    """
    Search the active product catalog using structured filters.
    """

    return product_service.search_products(
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        limit=limit,
    )


@mcp.tool()
def get_product_details(
    product_id: int,
) -> dict:
    """
    Get authoritative details for a single product.
    """

    return product_service.get_product_details(
        product_id=product_id,
    )

@mcp.tool()
def get_warranty_details(
    customer_id: int,
    order_number: str,
) -> dict:
    """
    Get extended warranty ownership and validity information
    for a product purchased in a customer's order.
    """

    return warranty_service.get_warranty_details(
        customer_id=customer_id,
        order_number=order_number,
    )

@mcp.tool()
def place_order(
    customer_id: int,
    product_id: int,
    quantity: int,
    address_id: int,
    ctx: Context,
) -> dict:
    """
    Place a single-product order for a customer.

    This tool must only be called after the customer has explicitly
    confirmed the product, quantity, and shipping address.

    The idempotency key is supplied by the calling application through
    MCP request metadata and is reused for retries of the same order request.
    
    """
    meta = ctx.request_context.meta or {}

    idempotency_key = meta.get(
        "idempotency_key"
    )

    if not idempotency_key:
        return {
            "success": False,
            "code": "MISSING_IDEMPOTENCY_KEY",
            "message": (
                "Order placement requires "
                "an application-generated idempotency key."
            ),
        }

    return order_service.place_order(
        customer_id=customer_id,
        product_id=product_id,
        quantity=quantity,
        address_id=address_id,
        idempotency_key=idempotency_key,
    )

@mcp.tool()
def get_order_details(
    customer_id: int,
    order_number: str,
) -> dict:
    """
    Get the details and itemized contents of a customer's order.

    Use this when the customer asks what products or items
    are included in a specific order.
    """

    return order_service.get_order_details(
        customer_id=customer_id,
        order_number=order_number,
    )

@mcp.tool()
def list_customer_addresses(
    customer_id: int,
) -> dict:
    """
    List the saved shipping addresses belonging to a customer.

    Use this before order placement to let the customer choose
    one of their existing saved shipping addresses.

    Do not ask the customer for an internal address_id.
    Do not create or modify addresses.
    """

    return order_service.list_customer_addresses(
        customer_id=customer_id,
    )

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8001,
    )