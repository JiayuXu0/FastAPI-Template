"""Unit tests for the response adapter helper."""

import json

import pytest

from schemas.base import Fail, Success, SuccessExtra
from utils.response_adapter import adapt_response

pytestmark = pytest.mark.unit


def test_adapt_response_handles_json_response():
    response = Success(code=201, msg="created", data={"id": 1})

    adapted = adapt_response(response)

    assert adapted == {"code": 201, "msg": "created", "data": {"id": 1}}


def test_adapt_response_handles_pure_dataclasses():
    class DummyResponse:
        code = 418
        msg = "teapot"
        data = {"answer": 42}
        total = 10
        page = 2
        page_size = 5

    adapted = adapt_response(DummyResponse())

    assert adapted == {
        "code": 418,
        "msg": "teapot",
        "data": {"answer": 42},
        "total": 10,
        "page": 2,
        "page_size": 5,
    }


def test_adapt_response_handles_success_extra_metadata():
    response = SuccessExtra(
        data=[1, 2],
        total=2,
        page=1,
        page_size=2,
        extra="value",
    )

    adapted = adapt_response(response)

    body = json.loads(response.body)
    assert adapted == body
    assert adapted["extra"] == "value"


def test_adapt_response_handles_failures():
    response = Fail(code=400, msg="bad request", data={"error": "missing"})

    assert adapt_response(response) == {
        "code": 400,
        "msg": "bad request",
        "data": {"error": "missing"},
    }
