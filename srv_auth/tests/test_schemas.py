import pytest
from pydantic import ValidationError

from srv_auth.src.modules.auth.schemas import (
    AuthLoginAdminReqSchema,
    AuthLoginReqSchema,
    AuthRegisterReqSchema,
)


class TestAuthLoginReqSchema:
    def test_valid(self):
        schema = AuthLoginReqSchema(number="+79991234567", password="secret123")
        assert schema.number == "+79991234567"
        assert schema.password == "secret123"

    def test_strips_spaces_from_phone(self):
        schema = AuthLoginReqSchema(number="+7 (999) 123-45-67", password="secret123")
        assert schema.number == "+79991234567"

    def test_strips_hyphens_from_phone(self):
        schema = AuthLoginReqSchema(number="+7-999-123-4567", password="secret123")
        assert schema.number == "+79991234567"

    def test_invalid_phone_no_plus(self):
        with pytest.raises(ValidationError):
            AuthLoginReqSchema(number="79991234567", password="secret123")

    def test_invalid_phone_too_short(self):
        with pytest.raises(ValidationError):
            AuthLoginReqSchema(number="+7999", password="secret123")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            AuthLoginReqSchema(number="+79991234567", password="short")

    def test_missing_number(self):
        with pytest.raises(ValidationError):
            AuthLoginReqSchema(password="secret123")

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            AuthLoginReqSchema(number="+79991234567")


class TestAuthRegisterReqSchema:
    def _make_valid(self, **overrides):
        data = {
            "number": "+79991234567",
            "password1": "secret123",
            "password2": "secret123",
            "email": "test@example.com",
            "country": "Russia",
            "city": "Moscow",
            "address": "Street 1",
        }
        data.update(overrides)
        return data

    def test_valid(self):
        schema = AuthRegisterReqSchema(**self._make_valid())
        assert schema.number == "+79991234567"

    def test_passwords_do_not_match(self):
        with pytest.raises(ValidationError, match="Passwords do not match"):
            AuthRegisterReqSchema(**self._make_valid(password1="secret123", password2="different123"))

    def test_password_with_spaces(self):
        with pytest.raises(ValidationError):
            AuthRegisterReqSchema(**self._make_valid(password1="with spaces", password2="with spaces"))

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            AuthRegisterReqSchema(**self._make_valid(password1="short", password2="short"))

    def test_invalid_phone(self):
        with pytest.raises(ValidationError):
            AuthRegisterReqSchema(**self._make_valid(number="123"))

    def test_strips_phone_formatting(self):
        schema = AuthRegisterReqSchema(**self._make_valid(number="+7 (999) 123-45-67"))
        assert schema.number == "+79991234567"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AuthRegisterReqSchema(**{})


class TestAuthLoginAdminReqSchema:
    def test_valid(self):
        schema = AuthLoginAdminReqSchema(login="admin", password="qwerty")
        assert schema.login == "admin"
        assert schema.password == "qwerty"

    def test_login_too_short(self):
        with pytest.raises(ValidationError):
            AuthLoginAdminReqSchema(login="adm", password="qwerty")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            AuthLoginAdminReqSchema(login="admin", password="qwe")

    def test_missing_login(self):
        with pytest.raises(ValidationError):
            AuthLoginAdminReqSchema(password="qwerty")

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            AuthLoginAdminReqSchema(login="admin")
