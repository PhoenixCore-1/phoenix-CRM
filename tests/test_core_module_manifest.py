from phoenix_crm.module import MODULE_CODE, MODULE_VERSION, module_manifest


def test_module_manifest_is_dependency_free_and_core_consumable():
    manifest = module_manifest()

    assert manifest["module"]["code"] == MODULE_CODE
    assert manifest["module"]["version"] == MODULE_VERSION
    assert manifest["integration"]["module_code"] == MODULE_CODE
    assert manifest["integration"]["version"] == MODULE_VERSION
    assert "crm.customer.v1" in manifest["integration"]["provided_contracts"]
    assert "crm.contact.v1" in manifest["integration"]["provided_contracts"]
    assert manifest["navigation"][0]["key"] == "crm.workspace"


def test_module_metadata_remains_stable():
    manifest = module_manifest()
    assert manifest["module"]["name"] == "CRM"
    assert manifest["module"]["description"] == "Phoenix CRM 360 V1.0"
