"""Phase 12 audit integration boundary tests."""

from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext
from phoenix_crm.services import CRMAuditService


def context(tenant_id, user_id, *resource_ids, correlation_id="corr-1"):
    return RequestContext(
        tenant=TenantContext(str(tenant_id)),
        user=UserContext(str(user_id)),
        access_scope=AccessScopeContext(resource_ids=frozenset(str(item) for item in resource_ids)),
        correlation_id=correlation_id,
    )


def test_context_audit_inherits_correlation_and_preserves_metadata():
    tenant = uuid4()
    user = uuid4()
    resource = uuid4()
    event = CRMAuditService.record(
        tenant_id=tenant,
        actor_user_id=user,
        action="customer.updated",
        resource_type="customer",
        resource_id=resource,
        metadata={"source": "crm"},
        request_context=context(tenant, user, resource, correlation_id="corr-42"),
    )
    assert event.correlation_id == "corr-42"
    assert event.metadata["source"] == "crm"


def test_context_audit_allows_system_event_without_actor():
    tenant = uuid4()
    event = CRMAuditService.record(
        tenant_id=tenant,
        actor_user_id=None,
        action="customer.sync.completed",
        resource_type="customer",
        request_context=context(tenant, uuid4(), correlation_id="sync-1"),
    )
    assert event.actor_user_id is None
    assert event.correlation_id == "sync-1"


def test_context_audit_rejects_resource_scope_even_when_resource_type_differs():
    tenant = uuid4()
    user = uuid4()
    with pytest.raises(PermissionError, match="outside request access scope"):
        CRMAuditService.record(
            tenant_id=tenant,
            actor_user_id=user,
            action="document.viewed",
            resource_type="document",
            resource_id=uuid4(),
            request_context=context(tenant, user),
        )
