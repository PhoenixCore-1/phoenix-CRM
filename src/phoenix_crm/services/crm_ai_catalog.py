"""Final CRM AI capability catalog and safety boundary for Phoenix CRM 360.

This module does not call providers or execute business actions. It provides a
stable CRM-owned catalogue of AI use cases so consumers can discover the
capabilities without depending on provider or implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from phoenix_crm.services.ai_intelligence import CRMIntelligenceType


@dataclass(frozen=True, slots=True)
class CRMAICapabilityDescriptor:
    """Stable metadata describing one CRM AI use case."""

    intelligence_type: CRMIntelligenceType
    proposal_only: bool = True
    requires_authorized_user_action: bool = True

    def __post_init__(self) -> None:
        if not self.proposal_only:
            raise ValueError("CRM AI capabilities must remain proposal-only")
        if not self.requires_authorized_user_action:
            raise ValueError("CRM AI capabilities require authorized user action")


class CRMAICapabilityCatalog:
    """Expose the complete CRM AI V1.0 capability set."""

    _CAPABILITIES: ClassVar[tuple[CRMAICapabilityDescriptor, ...]] = tuple(
        CRMAICapabilityDescriptor(item) for item in CRMIntelligenceType
    )

    @classmethod
    def all(cls) -> tuple[CRMAICapabilityDescriptor, ...]:
        """Return the immutable catalogue in deterministic enum order."""
        return cls._CAPABILITIES

    @classmethod
    def supports(cls, intelligence_type: CRMIntelligenceType) -> bool:
        """Return whether CRM exposes the requested AI use case."""
        return any(item.intelligence_type is intelligence_type for item in cls._CAPABILITIES)

    @classmethod
    def descriptor(cls, intelligence_type: CRMIntelligenceType) -> CRMAICapabilityDescriptor:
        """Return the descriptor for a supported CRM AI use case."""
        for item in cls._CAPABILITIES:
            if item.intelligence_type is intelligence_type:
                return item
        raise ValueError(f"unsupported CRM AI intelligence type: {intelligence_type}")
