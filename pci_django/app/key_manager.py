from __future__ import annotations

import os
import base64
from abc import ABC, abstractmethod
from typing import Optional


class KeyManager(ABC):
    @abstractmethod
    def get_data_encryption_key(self) -> bytes:
        """Return the 32-byteDEK for AES-256 encryption."""
        ...

    @abstractmethod
    def rotate_data_encryption_key(self) -> bytes:
        """Generate a new DEK, wrap it with the KEK, store it, return plaintext DEK.
        Caller is responsible for re-encrypting all stored ciphertext with the new DEK.
        """
        ...

    def description(self) -> str:
        """Return a description of the key manager."""
        return self.__class__.__name__ 
    

class LocalKeyManager(KeyManager):
    def __init__(self):
        self._kek = self._load_key("MASTER_KEY")
        self._dek = self._load_key("DATA_ENCRYPTION_KEY")

    @staticmethod
    def _load_key(env_var: str) -> bytes:
        raw = os.getenv(env_var)
        if not raw or len(raw) != 64:
            raise EnvironmentError(
                f"{env_var} must be a 64-character hex string (32 bytes)."
                f"Generate with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return bytes.fromhex(raw)
    
    def get_data_encryption_key(self) -> bytes:
        return self._dek
    
    def get_rotate_data_encryption_key(self) -> bytes:
        import secrets
        new_dek = secrets.token_bytes(32)
        self._dek = new_dek
        return new_dek
    
    def description(self) -> str:
        return "LocalKeyManager (environment variables — dev/demo only)"

