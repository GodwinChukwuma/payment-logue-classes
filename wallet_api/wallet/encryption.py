from __future__ import annotations

import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

_IV_LENGTH = 12
_TAG_LENGTH = 16

def encrypt_field(plaintext: str) -> str:
    """
    Encrypt a string field with AES-256-GCM
    Return a base64 encoded string safe to store in any text column
    """
    key = settings.AES_ENCRYPTION_KEY
    iv = os.urandom(_IV_LENGTH)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None) # ctb include the tag
    return base64.b64encode(iv + ct).decode()


def decrypt_field(ciphertext: str) -> str:
    """"
    Decrypt a value produced by encrypt_field()
    Raises ValueError on tampered or malformed data.
    """
    key = settings.AES_ENCRYPTION_KEY
    raw = base64.b64decode(ciphertext)
    iv = raw[:_IV_LENGTH]
    ct = raw[_IV_LENGTH:]
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(iv, ct, None).decode()
    except Exception as exc:
        raise ValueError("Decryption failed - data may be tampered or key is wrong.") from exc