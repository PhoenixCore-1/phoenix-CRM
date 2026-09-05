"""Tests for Phase 7.3 customer potential qualification service."""

from uuid import uuid4

import pytest

from phoenix_crm.domain import CustomerPotential, PotentialPriority, PotentialSource, PotentialStatus
from phoenix_crm.services import PotentialQualificationService


def make_potential(**kwargs) -> CustomerPotential:
    return CustomerPotential(
        tenant_id=kwargs.pop("tenant_id", uuid4()),
        customer_id=kwargs.pop("customer_id", uuid4()),
        solution_name=kwargs.pop("solution_name", "Chemical Anchoring"),
        reason=kwargs.pop("reason", "Customer currently uses a competing system"),
        source=kwargs.pop("source", PotentialSource.CUSTOMER_ACTIVITY),
        **kwargs,
    )


def test_start_returns_qualifying_result():
    potential = make_potential()
    result = PotentialQualificationService.start(potential)
    assert result.potential_id == potential.id
    assert result.status is PotentialStatus.QUALIFYING
    assert result.changed is True


def test_qualify_accepts_qualifying_potential():
    potential = make_potential()
    PotentialQualificationService.start(potential)
    result = PotentialQualificationService.qualify(potential)
    assert result.status is PotentialStatus.QUALIFIED
    assert result.changed is True


def test_qualify_accepts_identified_potential():
    potential = make_potential()
    result = PotentialQualificationService.qualify(potential)
    assert result.status is PotentialStatus.QUALIFIED


def test_realize_requires_qualified_state():
    potential = make_potential()
    with pytest.raises(ValueError, match="Only qualified potential"):
        PotentialQualificationService.realize(potential)


def test_realize_returns_realized_result():
    potential = make_potential()
    PotentialQualificationService.qualify(potential)
    result = PotentialQualificationService.realize(potential)
    assert result.status is PotentialStatus.REALIZED


def test_decline_returns_declined_result():
    potential = make_potential()
    result = PotentialQualificationService.decline(potential)
    assert result.status is PotentialStatus.DECLINED


def test_close_returns_closed_result():
    potential = make_potential()
    result = PotentialQualificationService.close(potential)
    assert result.status is PotentialStatus.CLOSED


def test_set_priority_returns_current_status():
    potential = make_potential()
    result = PotentialQualificationService.set_priority(potential, PotentialPriority.HIGH)
    assert potential.priority is PotentialPriority.HIGH
    assert result.status is PotentialStatus.IDENTIFIED
    assert result.changed is True


def test_update_context_strips_reason_and_context():
    potential = make_potential()
    result = PotentialQualificationService.update_context(
        potential,
        reason="  New requirement  ",
        context="  Tender starting soon  ",
    )
    assert potential.reason == "New requirement"
    assert potential.context == "Tender starting soon"
    assert result.status is PotentialStatus.IDENTIFIED


def test_update_context_rejects_blank_reason():
    potential = make_potential()
    with pytest.raises(ValueError, match="Potential reason cannot be empty"):
        PotentialQualificationService.update_context(potential, reason="   ")


def test_terminal_potential_cannot_be_closed_again():
    potential = make_potential()
    PotentialQualificationService.decline(potential)
    with pytest.raises(ValueError, match="already terminal"):
        PotentialQualificationService.close(potential)


def test_realized_potential_cannot_be_realized_again():
    potential = make_potential()
    PotentialQualificationService.qualify(potential)
    PotentialQualificationService.realize(potential)
    with pytest.raises(ValueError, match="Only qualified potential"):
        PotentialQualificationService.realize(potential)


def test_declined_potential_cannot_be_realized():
    potential = make_potential()
    PotentialQualificationService.decline(potential)
    with pytest.raises(ValueError, match="Only qualified potential"):
        PotentialQualificationService.realize(potential)
