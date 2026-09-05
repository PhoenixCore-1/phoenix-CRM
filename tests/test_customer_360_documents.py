from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.services import Customer360DocumentsService, Customer360Reference


def context(tenant_id, customer_id):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(uuid4())),
        access_scope=AccessScopeContext(resource_ids=frozenset({str(customer_id)})),
    )


def test_build_customer_documents_as_read_only_references():
    tenant_id, customer_id = uuid4(), uuid4()
    document = Customer360Reference("core", "document", uuid4(), "Contract", "active")
    section = Customer360DocumentsService.build(
        tenant_id=tenant_id,
        customer_id=customer_id,
        document_references=(document,),
    )
    assert section.available is True
    assert section.documents == (document,)


def test_build_filters_non_document_references():
    tenant_id, customer_id = uuid4(), uuid4()
    document = Customer360Reference("core", "document", uuid4(), "Quote", "active")
    ignored = Customer360Reference("sales", "opportunity", uuid4(), "Opportunity", "open")
    section = Customer360DocumentsService.build(
        tenant_id=tenant_id,
        customer_id=customer_id,
        document_references=(ignored, document),
    )
    assert section.documents == (document,)


def test_build_enforces_core_scope():
    tenant_id, customer_id = uuid4(), uuid4()
    with pytest.raises(PermissionError):
        Customer360DocumentsService.build(
            tenant_id=tenant_id,
            customer_id=customer_id,
            request_context=context(tenant_id, uuid4()),
        )


def test_build_gracefully_handles_unavailable_document_capability():
    tenant_id, customer_id = uuid4(), uuid4()
    section = Customer360DocumentsService.build(
        tenant_id=tenant_id,
        customer_id=customer_id,
    )
    assert section.available is False
    assert section.documents == ()


def test_provider_is_optional_and_contract_based():
    tenant_id, customer_id = uuid4(), uuid4()

    class Provider:
        def references_for_customer(self, *, tenant_id, customer_id):
            return (Customer360Reference("core", "customer_document", uuid4(), "Provider Doc"),)

    section = Customer360DocumentsService.build(
        tenant_id=tenant_id,
        customer_id=customer_id,
        provider=Provider(),
    )
    assert section.available is True
    assert [item.label for item in section.documents] == ["Provider Doc"]


def test_build_orders_documents_deterministically_without_mutating_inputs():
    tenant_id, customer_id = uuid4(), uuid4()
    document_b = Customer360Reference("core", "document", uuid4(), "Beta")
    document_a = Customer360Reference("core", "document", uuid4(), "Alpha")
    refs = (document_b, document_a)
    section = Customer360DocumentsService.build(
        tenant_id=tenant_id,
        customer_id=customer_id,
        document_references=refs,
    )
    assert [item.label for item in section.documents] == ["Alpha", "Beta"]
    assert refs == (document_b, document_a)


def test_build_is_read_only_for_document_references():
    tenant_id, customer_id = uuid4(), uuid4()
    document = Customer360Reference("core", "document", uuid4(), "Contract", "active")
    before = document
    Customer360DocumentsService.build(
        tenant_id=tenant_id,
        customer_id=customer_id,
        document_references=(document,),
    )
    assert document == before
