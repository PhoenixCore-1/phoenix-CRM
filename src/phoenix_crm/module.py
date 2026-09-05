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
