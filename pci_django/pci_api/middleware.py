from __future__ import annotations
import logging
import time

logger = logging.getLogger("pci_audit")

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        # response["Content-Security-Policy"] = "default-src 'none'"
        response["Referrer-Policy"] = "no-referrer"
        response["cache-control"] = "no-cache, no-store, must-revalidate, private"
        response["pragma"] = "no-cache"
        response["X-permitted-cross-domain-policies"] = "none"


        if "server" in response:
            del response["server"]
        if "x-powered-by" in response:
            del response["x-powered-by"]
        return response

class RequestLoggingMiddleware:
    "One audit log line per request"
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000)

        logger.info(
            "http.request",
            extra={
                "method": request.method,
                "path": request.path,
                "ip": _get_ip(request),
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response

def _get_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
