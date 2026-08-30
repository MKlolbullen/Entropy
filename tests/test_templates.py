from lnkup.core.templates import built_in_templates


def test_builtin_templates_are_valid():
    templates = built_in_templates()
    assert len(templates) >= 3
    for template in templates:
        template.scope()
