import uuid

from commerce_mcp.repositories.order_repository import OrderRepository


def unique_key(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def test_place_order_success():
    repo = OrderRepository()

    result = repo.place_order(
        customer_id=1,
        product_id=6,
        quantity=1,
        address_id=1,
        idempotency_key=unique_key("success"),
    )

    assert result["status"] == "ORDER_PLACED"
    assert result["order_number"].startswith("ORD-")
    assert result["total_amount"] > 0


def test_place_order_idempotency():
    repo = OrderRepository()

    key = unique_key("idempotent")

    first = repo.place_order(
        customer_id=1,
        product_id=6,
        quantity=1,
        address_id=1,
        idempotency_key=key,
    )

    second = repo.place_order(
        customer_id=1,
        product_id=6,
        quantity=1,
        address_id=1,
        idempotency_key=key,
    )

    assert first["status"] == "ORDER_PLACED"
    assert second["status"] == "ALREADY_PROCESSED"
    assert second["order"]["order_number"] == first["order_number"]


def test_place_order_wrong_address_owner():
    repo = OrderRepository()

    result = repo.place_order(
        customer_id=1,
        product_id=6,
        quantity=1,
        address_id=3,  # belongs to customer 2
        idempotency_key=unique_key("wrong-address"),
    )

    assert result["status"] == "ADDRESS_NOT_FOUND_OR_NOT_ACCESSIBLE"


def test_place_order_product_not_found():
    repo = OrderRepository()

    result = repo.place_order(
        customer_id=1,
        product_id=999999,
        quantity=1,
        address_id=1,
        idempotency_key=unique_key("missing-product"),
    )

    assert result["status"] == "PRODUCT_NOT_FOUND"


def test_place_order_insufficient_stock():
    repo = OrderRepository()

    result = repo.place_order(
        customer_id=1,
        product_id=3,  # HP Envy 14 has stock_quantity = 0
        quantity=1,
        address_id=1,
        idempotency_key=unique_key("no-stock"),
    )

    assert result["status"] == "INSUFFICIENT_STOCK"
    assert result["available_stock"] == 0