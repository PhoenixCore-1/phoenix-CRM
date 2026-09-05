from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from phoenix_crm.services import (
    CRMAICapabilityCatalog,
    CRMAICapabilityDescriptor,
    CRMIntelligenceType,
)


def test_catalog_contains_every_crm_ai_capability() -> None:
    descriptors = CRMAICapabilityCatalog.all()
    assert tuple(item.intelligence_type for item in descriptors) == tuple(CRMIntelligenceType)
    assert len(descriptors) == 7


def test_catalog_descriptors_are_proposal_only_and_require_authorization() -> None:
    assert all(item.proposal_only for item in CRMAICapabilityCatalog.all())
    assert all(item.requires_authorized_user_action for item in CRMAICapabilityCatalog.all())


def test_catalog_is_immutable() -> None:
    descriptor = CRMAICapabilityCatalog.all()[0]
    with pytest.raises(FrozenInstanceError):
        descriptor.proposal_only = False  # type: ignore[misc]


def test_catalog_supports_known_types() -> None:
    for intelligence_type in CRMIntelligenceType:
        assert CRMAICapabilityCatalog.supports(intelligence_type)


def test_catalog_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="unsupported CRM AI intelligence type"):
        CRMAICapabilityCatalog.descriptor("unknown")  # type: ignore[arg-type]


def test_descriptor_cannot_disable_proposal_only() -> None:
    with pytest.raises(ValueError, match="proposal-only"):
        CRMAICapabilityDescriptor(CRMIntelligenceType.CUSTOMER_SUMMARY, proposal_only=False)


def test_descriptor_cannot_disable_authorized_action_requirement() -> None:
    with pytest.raises(ValueError, match="authorized user action"):
        CRMAICapabilityDescriptor(
            CRMIntelligenceType.CUSTOMER_SUMMARY,
            requires_authorized_user_action=False,
        )
