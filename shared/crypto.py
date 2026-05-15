"""Шифрование (shared)."""

import base64
import os
from pathlib import Path
from typing import Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False


class TokenVault:
    """Хранилище для зашифрованных токенов."""
    
    _fernet: Optional[Fernet] = None
    _key_file: Path = Path(__file__).parent / ".vault_key"

    @classmethod
    def _get_fernet(cls) -> Optional[Fernet]:
        """Возвращает инициализированный Fernet."""
        if cls._fernet is not None:
            return cls._fernet

        if not _CRYPTO_AVAILABLE:
            return None

        if cls._key_file.exists():
            key = cls._key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            cls._key_file.write_bytes(key)

        cls._fernet = Fernet(key)
        return cls._fernet

    @classmethod
    def encrypt(cls, value: str) -> str:
        """Шифрует строку."""
        if not value:
            return ""
        fernet = cls._get_fernet()
        if fernet is None:
            # Fallback: base64 если cryptography не установлен
            return base64.b64encode(value.encode()).decode()
        return fernet.encrypt(value.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_value: str) -> str:
        """Расшифровывает строку."""
        if not encrypted_value:
            return ""
        fernet = cls._get_fernet()
        if fernet is None:
            # Fallback: base64 если cryptography не установлен
            try:
                return base64.b64decode(encrypted_value.encode()).decode()
            except Exception:
                return ""
        try:
            return fernet.decrypt(encrypted_value.encode()).decode()
        except Exception:
            # Если не удалось расшифровать — возможно, это старый base64
            try:
                return base64.b64decode(encrypted_value.encode()).decode()
            except Exception:
                return ""
