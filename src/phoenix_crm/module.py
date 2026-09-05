"""Phoenix CRM 360 module registration contract."""

MODULE_CODE = "crm"
MODULE_NAME = "CRM"
MODULE_VERSION = "1.0.0"


def module_metadata() -> dict[str, str]:
    """Return stable module metadata for Phoenix Core integration."""
    return {
        "code": MODULE_CODE,
        "name": MODULE_NAME,
        "version": MODULE_VERSION,
    }


def module_manifest() -> dict[str, object]:
    """Return the dependency-free published manifest consumed by Phoenix Core."""
    return {
        "module": {
            "code": MODULE_CODE,
            "name": MODULE_NAME,
            "version": MODULE_VERSION,
            "description": "Phoenix CRM 360 V1.0",
            "required_permissions": ("crm.view",),
            "required_entitlements": ("crm",),
            "navigation_keys": ("crm.workspace",),
            "capabilities": ("crm.customer_context",),
        },
        "integration": {
            "module_code": MODULE_CODE,
            "version": MODULE_VERSION,
            "provided_contracts": ("crm.customer.v1", "crm.contact.v1"),
            "provided_capabilities": ("crm.customer_context",),
        },
        "navigation": (
            {
                "key": "crm.workspace",
                "label": "CRM",
                "route": "/modules/crm",
                "module_code": MODULE_CODE,
                "permission": "crm.view",
                "entitlement": "crm",
            },
        ),
    }
