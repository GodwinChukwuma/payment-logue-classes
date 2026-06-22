from __future__ import annotations
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    Throttled,
    NotAuthenticated,
)
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

import logging

logger = logging.getLogger("wallet_audit")

class ConflictException(APIException):
    status_code = 409
    default_detail = "Conflict"
    default_code = "CONFLICT"

def error_response(
        code: str,
        message: str,
        http_status: int,
        details=None
) -> Response:
    """Return a consistently shaped error response."""
    body = {"success": False, "error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return Response(body, status=http_status)


def wallet_exception_handler(exc, context):
    """Custom DRF excepion handler."""
    response = exception_handler(exc, context)
    request = context.get("request")
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")) if request else ""

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        logger.warning("auth.failed", extra={"ip": ip, "reason":str(exc)})
        return error_response(
            "AUTHENTICATION_ERROR",
            "Authentication required. Provide a valid API key.",
            status.HTTP_401_UNAUTHORIZED,
        )
    
    if isinstance(exc, (AuthenticationFailed, InvalidToken)):
        logger.warning("auth.fialed", extra={"ip": ip, "reason": str(exc)})
        if response is None:
            response.data = {
                "success": False,
                "error": {
                    "code": "API_ERROR",
                    "message": str(exc),
                    "details": response.data
                }
            }
        return response

    if isinstance(exc, PermissionDenied):
        logger.warning("permission.denied", extra={"ip": ip})
        return error_response(
            "PERMISSION_ERROR",
            "You do not have permission to perform this action.",
            status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, NotFound):
        return error_response(
            "NOT FOUND",
            "The requested resource does not exist.",
            status.HTTP_404_NOT_FOUND,
        )
    
    if isinstance(exc, MethodNotAllowed):
        return error_response(
            "METHOD_NOT_ALLOWED",
            f"Method '{exc.args[0]}' not allowed on this endpoint.",
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    if isinstance(exc, ValidationError):
        details = _flatten_drf_errors(exc.detail)
        return error_response(
            "VALIDATION_ERROR",
            "Request validation failed.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )

    if isinstance(exc, Throttled):
        return error_response(
            "RATE_LIMIT_ERROR",
            "Too many requests. Please wait before trying again.",
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if isinstance(exc, ConflictException):
        logger.warning(
            "conflict.error",
            extra={"ip": ip, "reason": str(exc)}, 
        )

        return error_response(
            "CONFLICT",
            str(exc),
            status.HTTP_409_CONFLICT,
        )

    if response is not None:
        return response
    
    logger.error(
        "unhandled.exception",
        extra={"ip": ip, "error": repr(exc)},
        exc_info=exc,
    )
    return error_response(
        "INTERNAL_ERROR",
        "An internal server error occurred. Please try again later.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

def _flatten_drf_errors(detail):
    messages = []

    if isinstance(detail, list):
        for item in detail:
            messages.extend(_flatten_drf_errors(item))
    elif isinstance(detail, dict):
        for field_name, errors in detail.items():
            for err in _flatten_drf_errors(errors):
                messages.append(f"{field_name}: {err}")
    else:
        messages.append(str(detail))
    return messages

# def _get_ip(request):
#     forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
#     if forwarded:
#         return forwarded.split(",")[0].strip()
#     return request.META.get("REMOTE_ADDR", "unknown")