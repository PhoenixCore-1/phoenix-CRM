"""Phase 12 Core request/access contract hardening tests."""

from uuid import uuid4

import pytest

from phoenix_crm.api import AccessScopeContext, RequestContext, TenantContext, UserContext


def test_tenant_and_user_context_normalize_identifiers():
    assert TenantContext(" tenant-1 ").tenant_id == "tenant-1"
    assert UserContext(" user-1 ").user_id == "user-1"


def test_tenant_and_user_context_reject_blank_identifiers():
    with pytest.raises(ValueError, match="tenant_id"):
        TenantContext("   ")
    with pytest.raises(ValueError, match="user_id"):
        UserContext("   ")


def test_access_scope_normalizes_ids_and_rejects_empty_ids():
    scope = AccessScopeContext(resource_ids=frozenset({" customer-1 ", "customer-2"}))
    assert scope.resource_ids == frozenset({"customer-1", "customer-2"})
    assert scope.can_access_resource(" customer-1 ")

    with pytest.raises(ValueError, match="resource_ids"):
        AccessScopeContext(resource_ids=frozenset({""}))


def test_request_metadata_is_copied_and_immutable():
    metadata = {"source": "test"}
    context = RequestContext(
        tenant=TenantContext(str(uuid4())),
        user=UserContext(str(uuid4())),
        metadata=metadata,
    )
    metadata["source"] = "changed"
    assert context.metadata["source"] == "test"
    with pytest.raises(TypeError):
        context.metadata["new"] = "value"  # type: ignore[index]


def test_request_correlation_id_is_normalized():
    context = RequestContext(
        tenant=TenantContext(str(uuid4())),
        user=UserContext(str(uuid4())),
        correlation_id=" corr-123 ",
    )
    assert context.correlation_id == "corr-123"


def test_request_rejects_empty_metadata_keys():
    with pytest.raises(ValueError, match="metadata keys"):
        RequestContext(
            tenant=TenantContext(str(uuid4())),
            user=UserContext(str(uuid4())),
            metadata={"   ": "value"},
        )
