import pytest
from apps.access.qr import generate_entry_token, generate_session_token, verify_token, QRTokenError


@pytest.fixture
def mock_keys(settings):
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings.QR_PRIVATE_KEY = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    settings.QR_PUBLIC_KEY = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return settings.QR_PRIVATE_KEY, settings.QR_PUBLIC_KEY


class TestEntryToken:
    def test_generate_and_verify_entry_token(self, mock_keys):
        token = generate_entry_token(user_id=1, vehicle_id=2, campus_id=3)
        payload = verify_token(token, expected_type='entry')
        assert payload['user_id'] == 1
        assert payload['vehicle_id'] == 2
        assert payload['campus_id'] == 3
        assert payload['type'] == 'entry'

    def test_entry_token_wrong_type_raises(self, mock_keys):
        token = generate_entry_token(user_id=1, vehicle_id=2, campus_id=3)
        with pytest.raises(QRTokenError, match='tipo'):
            verify_token(token, expected_type='exit')

    def test_expired_entry_token_raises(self, mock_keys, settings):
        settings.QR_ENTRY_TOKEN_LIFETIME_SECONDS = -1
        token = generate_entry_token(user_id=1, vehicle_id=2, campus_id=3)
        with pytest.raises(QRTokenError, match='expirado'):
            verify_token(token, expected_type='entry')


class TestSessionToken:
    def test_generate_and_verify_session_token(self, mock_keys):
        token = generate_session_token(user_id=1, access_record_id=99, campus_id=3)
        payload = verify_token(token, expected_type='exit')
        assert payload['user_id'] == 1
        assert payload['access_record_id'] == 99
        assert payload['type'] == 'exit'

    def test_tampered_token_raises(self, mock_keys):
        token = generate_entry_token(user_id=1, vehicle_id=2, campus_id=3)
        tampered = token[:-10] + 'AAAAAAAAAA'
        with pytest.raises(QRTokenError, match='inválido'):
            verify_token(tampered, expected_type='entry')
