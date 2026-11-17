from app.redactor import PIIRedactor


def test_pii_redaction_and_restoration():
    redactor = PIIRedactor()
    original = "Send invoice to jane@company.ie for IBAN IE29AIBK93115212345678."

    sanitized, mapping, types = redactor.redact(original)

    assert "jane@company.ie" not in sanitized
    assert "IE29AIBK93115212345678" not in sanitized
    assert "EMAIL" in types
    assert "IBAN" in types

    restored = redactor.restore(sanitized, mapping)
    assert restored == original
