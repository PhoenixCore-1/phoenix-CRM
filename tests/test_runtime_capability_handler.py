from phoenix_crm.api.published import CustomerContext, CustomerReference
from phoenix_crm.integrations.runtime import CRMPublishedCapabilityHandler


class Provider:
    def __init__(self):
        self.calls = []

    def get_customer(self, *, tenant_id, customer_id):
        self.calls.append(("customer", tenant_id, customer_id))
        return CustomerReference(tenant_id, customer_id, "Acme")

    def get_customer_context(self, *, tenant_id, customer_id):
        self.calls.append(("context", tenant_id, customer_id))
        return CustomerContext(
            tenant_id=tenant_id,
            customer=CustomerReference(tenant_id, customer_id, "Acme"),
        )


class Context:
    organisation_id = "tenant-1"


def test_published_handler_routes_customer_operation():
    provider = Provider()
    result = CRMPublishedCapabilityHandler(provider)(
        operation="get_customer",
        context=Context(),
        payload={"customer_id": "customer-1"},
    )
    assert result.customer_id == "customer-1"
    assert provider.calls == [("customer", "tenant-1", "customer-1")]


def test_published_handler_routes_context_operation():
    provider = Provider()
    result = CRMPublishedCapabilityHandler(provider)(
        operation="get_customer_context",
        context=Context(),
        payload={"customer_id": "customer-1"},
    )
    assert result.customer.customer_id == "customer-1"


def test_published_handler_rejects_missing_customer_id():
    provider = Provider()
    try:
        CRMPublishedCapabilityHandler(provider)(
            operation="get_customer",
            context=Context(),
            payload={},
        )
    except ValueError as exc:
        assert str(exc) == "customer_id is required"
    else:
        raise AssertionError("Expected missing customer_id to fail")


def test_published_handler_rejects_unknown_operation():
    provider = Provider()
    try:
        CRMPublishedCapabilityHandler(provider)(
            operation="delete_customer",
            context=Context(),
            payload={"customer_id": "customer-1"},
        )
    except ValueError as exc:
        assert str(exc) == "Unsupported CRM operation: delete_customer"
    else:
        raise AssertionError("Expected unknown operation to fail")
