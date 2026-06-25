import uuid
from datetime import datetime, timezone, timedelta

import jwt
from django.conf import settings


class QRTokenError(Exception):
    pass


def _private_key() -> str:
    key = settings.QR_PRIVATE_KEY
    if not key:
        raise RuntimeError('QR_PRIVATE_KEY no configurada.')
    return key


def _public_key() -> str:
    key = settings.QR_PUBLIC_KEY
    if not key:
        raise RuntimeError('QR_PUBLIC_KEY no configurada.')
    return key


def generate_entry_token(user_id: int, vehicle_id: int, campus_id: int) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        'type': 'entry',
        'user_id': user_id,
        'vehicle_id': vehicle_id,
        'campus_id': campus_id,
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': now + timedelta(seconds=settings.QR_ENTRY_TOKEN_LIFETIME_SECONDS),
    }
    return jwt.encode(payload, _private_key(), algorithm='RS256')


def generate_session_token(user_id: int, access_record_id: int, campus_id: int) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        'type': 'exit',
        'user_id': user_id,
        'access_record_id': access_record_id,
        'campus_id': campus_id,
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': now + timedelta(seconds=settings.QR_SESSION_TOKEN_LIFETIME_SECONDS),
    }
    return jwt.encode(payload, _private_key(), algorithm='RS256')


def verify_token(token_str: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token_str,
            _public_key(),
            algorithms=['RS256'],
            options={'require': ['exp', 'iat', 'jti', 'type']},
        )
    except jwt.ExpiredSignatureError:
        raise QRTokenError('Token QR expirado.')
    except jwt.InvalidTokenError:
        raise QRTokenError('Token QR inválido.')

    if payload.get('type') != expected_type:
        raise QRTokenError(f'Token de tipo incorrecto. Esperado: {expected_type}.')

    return payload
