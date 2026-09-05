from datetime import datetime, timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import CustomerPotential, PotentialPriority, PotentialSource, PotentialStatus


def make_potential(**overrides):
    values = {
        "tenant_id": uuid4(),
        "customer_id": uuid4(),
        "solution_name": "Chemical Anchoring",
        "reason": "Customer currently buys mechanical anchors",
        "source": PotentialSource.CUSTOMER_ACTIVITY,
    }
    values.update(overrides)
    return CustomerPotential(**values)


def test_potential_defaults_and_normalizes_text():
    potential = make_potential(
        solution_name="  Chemical Anchoring  ",
        reason="  Customer needs a higher performance solution  ",
        context="  High corrosion exposure  ",
        current_solution="  Mechanical Anchors  ",
    )

    assert potential.status is PotentialStatus.IDENTIFIED
    assert potential.priority is PotentialPriority.NORMAL
    assert potential.solution_name == "Chemical Anchoring"
    assert potential.reason == "Customer needs a higher performance solution"
    assert potential.context == "High corrosion exposure"
    assert potential.current_solution == "Mechanical Anchors"


def test_potential_requires_solution_and_reason():
    with pytest.raises(ValueError):
        make_potential(solution_name=" ")
    with pytest.raises(ValueError):
        make_potential(reason=" ")


def test_qualification_lifecycle_is_explicit():
    potential = make_potential()
    potential.start_qualification()
    assert potential.status is PotentialStatus.QUALIFYING

    potential.qualify()
    assert potential.status is PotentialStatus.QUALIFIED

    potential.realize()
    assert potential.status is PotentialStatus.REALIZED


def test_invalid_lifecycle_transitions_are_blocked():
    potential = make_potential()

    with pytest.raises(ValueError):
        potential.realize()

    potential.decline()
    with pytest.raises(ValueError):
        potential.qualify()


def test_close_and_decline_are_terminal():
    potential = make_potential()
    potential.close()
    assert potential.status is PotentialStatus.CLOSED

    with pytest.raises(ValueError):
        potential.start_qualification()


def test_priority_and_context_updates_change_timestamp():
    original = datetime(2020, 1, 1, tzinfo=timezone.utc)
    potential = make_potential(created_at=original, updated_at=original)

    potential.set_priority(PotentialPriority.HIGH)
    assert potential.priority is PotentialPriority.HIGH
    assert potential.updated_at > original

    potential.update_context("  New reason  ", "  New context  ")
    assert potential.reason == "New reason"
    assert potential.context == "New context"


def test_activity_relationship_is_idempotent_and_removable():
    potential = make_potential()
    activity_id = uuid4()

    potential.link_activity(activity_id)
    potential.link_activity(activity_id)
    assert potential.related_activity_ids == {activity_id}

    potential.unlink_activity(activity_id)
    assert potential.related_activity_ids == set()


def test_potential_is_tenant_and_customer_scoped():
    tenant_id = uuid4()
    customer_id = uuid4()
    potential = make_potential(tenant_id=tenant_id, customer_id=customer_id)

    assert potential.tenant_id == tenant_id
    assert potential.customer_id == customer_id
    assert potential.source is PotentialSource.CUSTOMER_ACTIVITY
