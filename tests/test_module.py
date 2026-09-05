from phoenix_crm.module import module_metadata


def test_module_metadata():
    assert module_metadata() == {
        "code": "crm",
        "name": "CRM",
        "version": "1.0.0",
    }
