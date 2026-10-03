"""
api.v1.utils - Utility functions for the v1 API
-----------------------------------------------

Functions:
    json(payload: object, status: int) -> Response:
        Build a JSON response with an explicit status code.

    error(message: str, status: int, **extra: object) -> Response:
        Build a JSON error response of the shape ``{"error": message, **extra}``.

    parse_body(model: type[ModelT], payload: object) -> ModelT | Response:
        Validate a JSON request body against a Pydantic model.
"""

import logging

from flask import Response, jsonify
from pydantic import BaseModel, ValidationError

_log = logging.getLogger(__name__)


def json(payload: object, status: int) -> Response:
    """Build a JSON response with an explicit status code.

    Args:
        payload (object): The JSON-serializable payload to return.
        status (int): The HTTP status code for the response.

    Returns:
        Response: The resulting Flask response.
    """
    response = jsonify(payload)
    response.status_code = status
    return response


def error(message: str, status: int, **extra: object) -> Response:
    """Build a JSON error response of the shape ``{"error": message, **extra}``.

    Args:
        message (str): A human-readable error message.
        status (int): The HTTP status code for the response.
        **extra (object): Any additional fields to merge into the error body
            (e.g. ``details`` for validation errors).

    Returns:
        Response: The resulting Flask error response.
    """
    return json({"error": message, **extra}, status)


def parse_body[ModelT: BaseModel](model: type[ModelT], payload: object) -> ModelT | Response:
    """Validate a request's JSON body against a Pydantic model.

    Args:
        model (type[ModelT]): The model to validate against.
        payload (object): The parsed JSON body (or None if missing/invalid JSON).

    Returns:
        ModelT | Response: The validated model instance, or a 400 error
        response if the body was missing, not valid JSON, or failed validation.
    """
    if payload is None:
        _log.error("Request body is missing or not valid JSON.")
        return error("Request body must be valid JSON.", 400)

    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_context=False)
        _log.error("Request body failed validation: %s", errors)
        return error("Invalid request data.", 400, details=errors)
