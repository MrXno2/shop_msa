from srv_auth.src.modules.auth.utils import hashed_pass, verify_password


class TestHashedPass:
    def test_returns_hash_string(self):
        result = hashed_pass("mypassword")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_different_calls_produce_different_hashes(self):
        hash1 = hashed_pass("mypassword")
        hash2 = hashed_pass("mypassword")
        assert hash1 != hash2

    def test_hash_is_bcrypt_format(self):
        result = hashed_pass("mypassword")
        assert result.startswith("$2")


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        password = "mypassword"
        hashed = hashed_pass(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hashed_pass("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password(self):
        hashed = hashed_pass("")
        assert verify_password("", hashed) is True
        assert verify_password("wrong", hashed) is False
