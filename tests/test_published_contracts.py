from phoenix_crm.api.published import (
    CRM_CONTACT_CONTRACT,
    CRM_CUSTOMER_CONTRACT,
    CRM_CUSTOMER_CONTEXT_CAPABILITY,
    ContactReference,
    CustomerContext,
    CustomerReference,
)


def test_published_crm_contract_identifiers_are_stable():
    assert CRM_CUSTOMER_CONTRACT == "crm.customer.v1"
    assert CRM_CONTACT_CONTRACT == "crm.contact.v1"
    assert CRM_CUSTOMER_CONTEXT_CAPABILITY == "crm.customer_context"


def test_customer_context_is_transport_neutral():
    customer = CustomerReference("tenant-1", "customer-1", "Example Customer")
    contact = ContactReference("tenant-1", "contact-1", "customer-1", "Jane Doe")
    context = CustomerContext("tenant-1", customer, primary_contact=contact)

    assert context.customer.customer_id == "customer-1"
    assert context.primary_contact.contact_id == "contact-1"
