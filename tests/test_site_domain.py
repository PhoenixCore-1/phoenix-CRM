from datetime import timezone
from uuid import uuid4

import pytest

from phoenix_crm.domain import CustomerSite, CustomerSiteStatus


def test_customer_site_defaults_to_active():
    site = CustomerSite(uuid4(), uuid4(), "Head Office")

    assert site.status is CustomerSiteStatus.ACTIVE
    assert site.id is not None
    assert site.created_at.tzinfo is timezone.utc


def test_customer_site_stores_location_details():
    site = CustomerSite(
        uuid4(),
        uuid4(),
        "Head Office",
        address_line_1="  10 Main Street  ",
        city="  Johannesburg ",
        state_province="Gauteng",
        postal_code="2000",
        country="South Africa",
    )

    assert site.address_line_1 == "10 Main Street"
    assert site.city == "Johannesburg"
    assert site.state_province == "Gauteng"
    assert site.postal_code == "2000"
    assert site.country == "South Africa"


def test_customer_site_rejects_empty_name():
    with pytest.raises(ValueError, match="Customer site name cannot be empty"):
        CustomerSite(uuid4(), uuid4(), "   ")


def test_customer_site_allows_optional_location_fields():
    site = CustomerSite(uuid4(), uuid4(), "Remote Site")

    assert site.address_line_1 is None
    assert site.city is None
    assert site.country is None


def test_customer_site_can_be_primary():
    site = CustomerSite(uuid4(), uuid4(), "Head Office")

    site.set_primary(True)

    assert site.is_primary is True


def test_customer_site_can_be_renamed():
    site = CustomerSite(uuid4(), uuid4(), "Old Site")
    original_timestamp = site.updated_at

    site.rename("New Site")

    assert site.name == "New Site"
    assert site.updated_at >= original_timestamp


def test_customer_site_rename_rejects_empty_name():
    site = CustomerSite(uuid4(), uuid4(), "Customer Site")

    with pytest.raises(ValueError, match="Customer site name cannot be empty"):
        site.rename(" ")


def test_customer_site_preserves_customer_and_tenant_identity():
    tenant_id = uuid4()
    customer_id = uuid4()
    site = CustomerSite(tenant_id, customer_id, "Branch")

    assert site.tenant_id == tenant_id
    assert site.customer_id == customer_id
