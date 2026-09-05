"""Tests for Phase 7.3 customer potential qualification service."""

from uuid import uuid4

import pytest

from phoenix_crm.domain import CustomerPotential, PotentialPriority, PotentialSource, PotentialStatus
from phoenix_crm.services import PotentialQualificationService


def make_potential() -> CustomerPotential:
    return CustomerPotential(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        solution_name="Chemical Anchoring",
        reason="Customer currently uses a competing system",
        source=PotentialSource.CUSTOMER_ACTIVITY,
    )


def test_start_returns_qualifying_result():
    potential = make_potential()
    result = PotentialQualificationService.start(potential)
    assert result.potential_id == potential.id
    assert result.status is PotentialStatus.QUALIFYING
    assert result.changed is True


def test_qualify_returns_qualified_result():
    potential = make_potential()
    PotentialQualificationService.start(potential)
    result = PotentialQualificationService.qualify(potential)
    assert result.status is PotentialStatus.QUALIFIED
    assert result.changed is True


def test_realize_requires_qualified_state():
    potential = make_potential()
    with pytest.raises(ValueError, match="Only qualified"):
        PotentialQualificationService.realize(potential)


def test_realize_returns_realized_result():
    potential = make_potential()
    PotentialQualificationService.start(potential)
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


def test_terminal_potential_cannot_be_closed_again():
    potential = make_potential()
    PotentialQualificationService.decline(potential)
    with pytest.raises(ValueError, match="already terminal"):
        PotentialQualificationService.close(potential)
