from __future__ import annotations
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

def _get_key() -> bytes:
    """Get the 32-byte AES key from settings."""
    key = settings.AES_ENCRYPTION_KEY
    if len(key) != 32:
        raise RuntimeError("AES_ENCRYPTION_KEY must be exactly 32 (64 hex chars.)")
    return key


def encrypt_field(plaintext: str) -> str:
    """
    Encrypt a plaintext using AES-256-GCM.
    Returns base64( IV(12 bytes) || ciphertext || GCM-tag(16 bytes) )

    Every call generates a fresh random 12-byte IV-ciphertext is differetn 
    every time even for the same plaintext
    """
    key = _get_key()
    iv = os.urandom(12)  # 12 bytes IV for GCM
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    combined = iv + ciphertext_with_tag
    return base64.b64encode(combined).decode("ascii")

def decrypt_field(stored_value: str) -> str:
    """
    Decrypt a value produced by encrypt_field.
    Raise:
        InvalidTag - if the ciphertext was tampered with (GCM auth failed)
        ValueError - if stored_value is malformed
    """""
    combined = base64.b64decode(stored_value)
    if len(combined) < 28:
        raise ValueError("Stored ciphertext is too short to be valid.")
    iv, ciphertext_with_tag = combined[:12], combined[12:]
    key = _get_key()
    aesgcm = AESGCM(key)
    plaintext_bytes = aesgcm.decrypt(iv, ciphertext_with_tag, None)
    return plaintext_bytes.decode("utf-8")

def mask_pan(pan: str) -> str:
    """Mask a PAN per the assignment spec: show only the last 4 digits"""
    pan = pan.replace(" ", "").replace("-", "")
    if len(pan) <= 4:
        return "*" * len(pan)
    return "*" * (len(pan) - 4) + pan[-4:]


