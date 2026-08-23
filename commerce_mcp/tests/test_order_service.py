from commerce_mcp.services.order_service import OrderService


class FakeOrderRepository:
    def __init__(self, result):
        self.result = result

    def get_order_status(self, customer_id, order_number):
        return self.result


def test_check_order_status_success():
    fake_repo = FakeOrderRepository(
        {
            "order": {
                "order_id": 1,
                "customer_id": 1,
                "order_status": "COMPLETED",
            },
            "shipments": [
                {
                    "shipment_id": 1,
                    "current_status": "DELIVERED",
                }
            ],
        }
    )

    service = OrderService(repository=fake_repo)

    result = service.check_order_status(
        customer_id=1,
        order_number="ORD-2026-000001",
    )

    assert result["success"] is True
    assert result["code"] == "ORDER_STATUS_FOUND"
    assert result["data"]["order"]["order_status"] == "COMPLETED"


def test_check_order_status_not_found():
    fake_repo = FakeOrderRepository(None)

    service = OrderService(repository=fake_repo)

    result = service.check_order_status(
        customer_id=2,
        order_number="ORD-2026-000002",
    )

    assert result["success"] is False
    assert result["code"] == "ORDER_NOT_FOUND_OR_NOT_ACCESSIBLE"