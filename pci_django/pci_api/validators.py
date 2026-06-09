from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List
from datetime import date

# Approved email domains
APPROVED_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "yahoo.co.in",
    "yahoo.fr",
    "yahoo.de",
    "yahoo.es",
    "yahoo.it",
    "yahoo.ca",
    "ymail.com",
    "outlook.com",
    "hotmail.com",
    "hotmail.co.uk",
    "hotmail.fr",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "protonmail.com",
    "proton.me",
    "aol.com",
}

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_EXPIRY_RE = re.compile(r"^(\d{2})/(\d{2}|\d{4})$")
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)

def _luhn(pan: str) -> bool:
    """Luhn algorithm - validate a PAN has a correct check digits."""
    digits = [int(d) for d in pan if d.isdigit()]
    if len(digits) < 13:
        return False
    digits.reverse()
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

def validate_transaction(data: dict) -> ValidationResult:
    """Validate all field for POST /processTransaction"""
    errors: List[str] = []
    pan_raw = data.get("pan", "")
    if not pan_raw:
        errors.append("pan: this field is required.")
    else:
        pan =re.sub(r"[\s\-]", "", str(pan_raw))
        if not pan.isdigit():
            errors.append("pan: must contain digits only.")
        elif not (13 <= len(pan) <= 19):
            errors.append("pan: must be between 13 and 19 digits.")
        elif not _luhn(pan):
            errors.append("pan: card number is invalid.")

    # Expiry date
    expiry_raw = str(data.get("expiry_date") or "").strip()
    if not expiry_raw:
        errors.append("expiry_date: this field is required (format MM/YY or MM/YYYY).")
    else:
        m = _EXPIRY_RE.match(expiry_raw)
        if not m:
            errors.append("expiry_date: invalid format - use MM/YY or MM/YYYY.")
        else:
            month = int(m.group(1))
            year_str = m.group(2)
            year = 2000 + int(year_str) if len(year_str) == 2 else int(year_str)
            if not (1 <= month <= 12):
                errors.append("expiry_date: month must be bettween 01 and 12.")
            else:
                today = date.today()
                if year < today.year or (year == today.year and month < today.month):
                    errors.append("expiry_date: card has expired.")

    # Amount
    amount_raw = data.get("amount")
    if amount_raw is None:
        errors.append("amount: this field is required.")
    else:
        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("amount: must be greater than 0.")
            elif amount > 1_000_000:
                errors.append("amount: exceeds the maximum single-transaction limit of 1,000,000.")
        except (TypeError, ValueError):
            errors.append("amount: must be a valid number.")

    # validate here, then discard. Never stored, never logged
    pin_raw = data.get("pin", "")
    if not pin_raw:
        errors.append("pin: this field is required.")
    else:
        pin = str(pin_raw)
        if not pin.isdigit():
            errors.append("pin: must contain digits only.")
        elif not(4 <= len(pin) <= 6):
            errors.append("pin: must be between 4 and 6 digits.")

    # email
    email_raw = data.get("email", "")
    if not email_raw:
        errors.append("email: this field is required.")
    else:
        email = str(email_raw).strip()
        if not _EMAIL_RE.match(email):
            errors.append("email: invalid format.")
        else:
            domain = email.split("@", 1)[1]
            if domain not in APPROVED_DOMAINS:
                errors.append(
                    f"email: '{domain}' is not an accepted email provider. "
                    f"Please use a Gmail, Yahoo, Outlook, Hotmail, iCloud, or ProtonMail address."
                )

    return ValidationResult(valid=len(errors) == 0, errors=errors)




