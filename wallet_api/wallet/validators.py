from __future__ import annotations

"""
Input validations for registration, PIN verification, and transactions amounts.
Centralised here so views stays thin and validation is tetsable in isolation
"""
import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import re


@dataclass
class ValidationResult:
    valid: bool = True
    errors: dict = field(default_factory=dict)

    def add(self, key: str, msg: str) -> None:
        self.valid = False
        self.errors.setdefault(key, []).append(msg)

_BVN_RE = re.compile(r"^\d{11}$")
_PIN_RE = re.compile(r"^\d{4,6}$")
_ACCOUNT_RE = re.compile(r"^\d{10}$")

def validate_registration(data: dict) -> ValidationResult:
    r = ValidationResult()

    if not data.get("full_name", "").strip():
        r.add("full_name", "Full name is required.")

    email = data.get("email", "")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        r.add("email", "A valid email address is required.")
    
    password = data.get("password", "")
    if len(password) < 8:
        r.add("password", "Password must be at least 8 characters long.")
    
    bvn = str(data.get("bevn", "")).strip()
    if not _BVN_RE.match(bvn):
        r.add("bvn", "BVN must be 11 digits long.")

    pin = str(data.get("pin", "")).strip()
    if not _PIN_RE.match(pin):
        r.add("pin", "PIN must be 4-6 digits long.")

    return r

def validate_amount(raw) -> tuple[bool, Decimal | None, str]:
    """Returs (is_valid, decimal_amount, error_message). Amount must be a positive number at most 2 decimal places"""
    try:
        amount = Decimal(str(raw)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return False, None, "Amount must be a valid number."
    if amount <= 0:
        return False, None, "Amount must be greater than 0."
    return True, amount, ""

def validate_transfer(data: dict) -> ValidationResult:
    r = ValidationResult()

    recipient = str(data.get("recipient_account_no", "")).strip()
    if not _ACCOUNT_RE.match(recipient):
        r.add("recipient_account_no", "Recipient account number must be 10 digits long.")

    ok, _, err = validate_amount(data.get("amount"))
    if not ok:
        r.add("amount", err)

    if not data.get("pin"):
        r.add("pin", "PIN is required to authoorize a transfer.")

    return r

def validate_withdrawal(data: dict) -> ValidationResult:
    r = ValidationResult()

    ok, _, err = validate_amount(data.get("amount"))
    if not ok:
        r.add("amount", err)

    if not data.get("bank_code", "").strip():
        r.add("bank_code", "Bank code is required.")

    if not data.get("account_number", "").strip():
        r.add("account_number", "Account number is required.")

    if not data.get("pin"):
        r.add("pin", "PIN is required to authoorize a withdrawal.")

    return r