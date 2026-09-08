from app.chat.validation import (
    looks_like_a_question,
    validate_contact_number,
    validate_email_field,
    validate_full_name,
)


class TestValidateFullName:
    def test_accepts_a_normal_name(self):
        ok, err = validate_full_name("Rabail Waqar")
        assert ok is True
        assert err is None

    def test_rejects_too_short(self):
        ok, err = validate_full_name("A")
        assert ok is False
        assert err is not None

    def test_rejects_known_placeholder_values(self):
        ok, _ = validate_full_name("test")
        assert ok is False

    def test_rejects_names_with_no_letters(self):
        ok, _ = validate_full_name("12345")
        assert ok is False

    def test_strips_whitespace_before_checking(self):
        ok, _ = validate_full_name("   Jane Doe   ")
        assert ok is True


class TestValidateEmailField:
    def test_accepts_a_valid_email(self):
        ok, normalized, err = validate_email_field("Rabail.Waqar@Example.com")
        assert ok is True
        assert err is None
        assert normalized is not None

    def test_rejects_missing_at_symbol(self):
        ok, normalized, err = validate_email_field("not-an-email")
        assert ok is False
        assert normalized is None
        assert err is not None

    def test_rejects_empty_string(self):
        ok, _, _ = validate_email_field("")
        assert ok is False


class TestValidateContactNumber:
    def test_accepts_numbers_with_country_code_and_spaces(self):
        ok, err = validate_contact_number("+92 300 1234567")
        assert ok is True
        assert err is None

    def test_accepts_us_style_formatting(self):
        ok, _ = validate_contact_number("+1 (555) 123-4567")
        assert ok is True

    def test_rejects_too_few_digits(self):
        ok, err = validate_contact_number("12345")
        assert ok is False
        assert err is not None

    def test_rejects_letters_only(self):
        ok, _ = validate_contact_number("call me maybe")
        assert ok is False


class TestLooksLikeAQuestion:
    def test_detects_question_mark(self):
        assert looks_like_a_question("What technologies do you use?") is True

    def test_plain_statement_is_not_a_question(self):
        assert looks_like_a_question("John Smith") is False

    def test_email_is_not_a_question(self):
        assert looks_like_a_question("john@example.com") is False