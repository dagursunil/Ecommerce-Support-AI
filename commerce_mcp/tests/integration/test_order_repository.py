from commerce_mcp.repositories.order_repository import OrderRepository


def test_get_order_status_success():
    repo = OrderRepository()

    result = repo.get_order_status(
        customer_id=1,
        order_number="ORD-2026-000001",
    )

    assert result is not None

    assert result["order"]["order_id"] == 1
    assert result["order"]["customer_id"] == 1
    assert result["order"]["order_status"] == "COMPLETED"

    assert len(result["shipments"]) == 1

    shipment = result["shipments"][0]

    assert shipment["tracking_number"] == "DHL-DE-100001"
    assert shipment["current_status"] == "DELIVERED"


def test_get_order_status_wrong_customer():
    repo = OrderRepository()

    result = repo.get_order_status(
        customer_id=3,
        order_number="ORD-2026-000002",
    )

    assert result is None


def test_get_order_status_split_shipment():
    repo = OrderRepository()

    result = repo.get_order_status(
        customer_id=3,
        order_number="ORD-2026-000003",
    )

    assert result is not None

    assert result["order"]["order_status"] == "CONFIRMED"

    assert len(result["shipments"]) == 2

    statuses = {
        shipment["current_status"]
        for shipment in result["shipments"]
    }

    assert statuses == {
        "IN_TRANSIT",
        "PACKED",
    }