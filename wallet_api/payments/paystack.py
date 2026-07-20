from __future__ import annotations

import os
import warnings
import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from django.conf import settings
from typing import Any
import ssl

import logging

logger = logging.getLogger("wallet_audit")

_BASE = "https://api.paystack.co"
_KOBO = 100 

import certifi
class _TLSAdapter(HTTPAdapter):
    """
    Forces TLSv1.2 for Paystack requests.
    Python 3.13 + OpenSSL 3.6 triggers SSLV3_ALERT_BAD_RECORD_MAC
    against some servers when using the default TLS negotiation.
    Pinning to TLSv1.2 avoids this.

    In development (DEBUG=True or PAYSTACK_VERIFY_SSL=false in .env):
        SSL verification is disabled. Safe for local testing — no real money.
 
    In production (DEBUG=False):
        Full SSL verification with certifi CA bundle.
    """
    def __init__(self, verify_ssl: bool = True, *args, **kwargs):
        self._verify_ssl = verify_ssl
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if self._verify_ssl:
            ctx = create_urllib3_context(ssl_minimum_version=ssl.TLSVersion.TLSv1_2)
            ctx.load_verify_locations(certifi.where())
            ctx.options |= ssl.OP_NO_RENEGOTIATION
            ctx.options |= ssl.OP_NO_TICKET 
            kwargs["ssl_context"] = ctx
        else:
            ctx = create_urllib3_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)

    def send(self, request, *args, **kwargs):
        if not self._verify_ssl:
            kwargs["verify"] = False
        return super().send(request, *args, **kwargs)
    
def _should_verify_ssl() -> bool:
    """
    Returns False in local dev to bypass the macOS/OpenSSL 3.6 TLS bug.
    Returns True in production (when DEBUG=False).
    Override explicitly with PAYSTACK_VERIFY_SSL=false in .env.
    """
    env_override = os.environ.get("PAYSTACK_VERIFY_SSL", "").lower()
    if env_override == "false":
        return False
    if env_override == "true":
        return True
    from django.conf import settings as _s
    return not _s.DEBUG


def _session() -> requests.Session:
    verify = _should_verify_ssl()
    if not verify:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    s = requests.Session()
    s.mount("https://api.paystack.co", _TLSAdapter(verify_ssl=verify))
    return s

def initialize_payment(email: str, amount_ngn: float, reference: str) -> tuple[bool, dict]:
    return _post("/transaction/initialize", {
        "email": email,
        "amount": int(amount_ngn * _KOBO),
        "reference": reference,
        "callback_url": settings.PAYSTACK_CALLBACK_URL,
        "metadata": {"reference": reference},
    })

def verify_payment(reference: str) -> tuple[bool, dict]:
    return _get(f"/transaction/verify/{reference}")

def get_banks(country: str = "nigeria") -> tuple[bool, list]:
    return _get("/bank", {"country": country, "perPage": 100})

def resolve_account(account_number: str, bank_code: str) -> tuple[bool, dict]:
    return _get("/bank/resolve", {"account_number": account_number, "bank_code": bank_code})

def create_transfer_recipient(
        account_number: str,
        account_name: str,
        bank_code: str,
) -> tuple[bool, dict]:
    return _post("/transferrecipient", {
        "type": "nuban",
        "name": account_name,
        "account_number": account_number,
        "bank_code": bank_code,
        "currency": "NGN",
    })

def initiate_transfer(
        amount_ngn: float,
        recipient_code: str,
        reference: str,
        reason: str = "Wallet withdrawal",
) -> tuple[bool, dict]:
    return _post("/transfer", {
        "source": "balance",
        "amount": int(amount_ngn * _KOBO),
        "recipient": recipient_code,
        "reference": reference,
        "reason": reason,
    })

def finalize_transfer(transfer_code: str, otp: str) -> tuple[bool, dict]:

    return _post(
        "/transfer/finalize_transfer",
        {
            "transfer_code": transfer_code,
            "otp": otp
        },
    )

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

def _post(path: str, payload: dict) -> tuple[bool, dict]:
    try:
        r = _session().post(f"{_BASE}{path}", json=payload, headers=_headers(), timeout=30)

        if not r.text.strip():
            if r.ok:
                return True, {}
            return False, {"error": f"Paystack returned HTTP {r.status_code} with empty body"}
        
        try:
            body = r.json()
        except Exception:
            logger.error("paystack.json_decode_failed", extra={
                "path": path,
                "status": r.status_code,
                "body": r.text[:500]
            })

            if r.ok:
                return True, {"raw": r.text}
            return False, {"error": f"Paystack returned non-JSON: r.text[:200]"}

        if r.ok and body.get("status"):
            return True, body.get("data", {})
        return False, {"error": body.get("message", "Paystack error")}
    except Exception as exc:
        logger.error("paystack.request_failed", extra={"path": path, "error": repr(exc)})
        return False, {"error": repr(exc)}

def _get(path: str, params: dict | None = None) -> tuple[bool, Any]:
    try:
        r = _session().get(f"{_BASE}{path}", params=params, headers=_headers(), timeout=30)
        body = r.json()
        if r.ok and body.get("status"):
            return True, body.get("data", {})
        return False, {"error": body.get("message", "Paystack error")}
    except Exception as exc:
        logger.error("paystack.request_failed", extra={"path": path, "error": repr(exc)})
        return False, {"error": repr(exc)}


