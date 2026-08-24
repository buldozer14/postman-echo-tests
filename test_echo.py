"""
Автотесты публичного сервиса https://postman-echo.com

Проверяется поведение, снятое вручную в Postman по эндпоинтам
  GET  https://postman-echo.com/get
  POST https://postman-echo.com/post

Эхо-сервис возвращает JSON с разобранным запросом, поэтому каждый тест
сравнивает отправленное с тем, что сервис отразил обратно.
"""

import pytest
import requests

BASE_URL = "https://postman-echo.com"
GET_URL = f"{BASE_URL}/get"
POST_URL = f"{BASE_URL}/post"
TIMEOUT = 15


@pytest.fixture(scope="session")
def session():
    with requests.Session() as s:
        s.headers.update({"User-Agent": "postman-echo-tests/1.0"})
        yield s


def test_get_query_params_are_echoed(session):
    """GET /get: одиночный и повторяющийся квери-параметры возвращаются в args."""
    params = {"foo": "bar", "lang": "ru", "x": ["1", "2"]}

    response = session.get(GET_URL, params=params, timeout=TIMEOUT)

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    body = response.json()
    assert body["args"]["foo"] == "BROKEN"
    assert body["args"]["lang"] == "ru"
    assert body["args"]["x"] == ["1", "2"]
    assert body["url"].startswith(GET_URL)
    # у GET-ответа нет полей тела запроса
    assert "form" not in body
    assert "data" not in body


def test_get_echoes_custom_headers(session):
    """GET /get: пользовательские заголовки возвращаются в headers в нижнем регистре.

    Внимание: заголовок X-Request-Id съедается edge-прокси сервиса и в эхо не
    попадает — проверяем на заголовках, которые сервис действительно отражает.
    """
    headers = {"X-Trace-Id": "abc-123", "X-Client": "pytest"}

    response = session.get(GET_URL, headers=headers, timeout=TIMEOUT)

    assert response.status_code == 200
    echoed = response.json()["headers"]
    assert echoed["x-trace-id"] == "abc-123"
    assert echoed["x-client"] == "pytest"
    assert echoed["host"] == "postman-echo.com"
    assert echoed["user-agent"] == "postman-echo-tests/1.0"
    assert echoed["x-forwarded-proto"] == "https"
    assert "X-Trace-Id" not in echoed


def test_post_form_urlencoded(session):
    """POST /post с form-data: тело попадает в form, data остаётся пустой строкой."""
    payload = {"login": "user", "password": "secret"}

    response = session.post(POST_URL, data=payload, timeout=TIMEOUT)

    assert response.status_code == 200
    body = response.json()
    assert body["form"] == payload
    assert body["data"] == ""
    assert body["files"] == {}
    assert body["args"] == {}
    assert body["headers"]["content-type"] == "application/x-www-form-urlencoded"


def test_post_json_body(session):
    """POST /post с JSON: тело возвращается и в json, и в data как объект."""
    payload = {"id": 42, "tags": ["qa", "api"], "nested": {"ok": True}}

    response = session.post(POST_URL, json=payload, timeout=TIMEOUT)

    assert response.status_code == 200
    body = response.json()
    assert body["json"] == payload
    assert body["data"] == payload
    assert body["form"] == {}
    assert body["headers"]["content-type"] == "application/json"
    assert body["headers"]["content-length"] == str(len(response.request.body))


def test_post_raw_text_body(session):
    """POST /post с text/plain: тело кладётся в data строкой, json = null."""
    text = "просто текст"

    response = session.post(
        POST_URL,
        data=text.encode("utf-8"),
        headers={"Content-Type": "text/plain; charset=utf-8"},
        timeout=TIMEOUT,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == text
    assert body["json"] is None
    assert body["form"] == {}


def test_post_multipart_file_upload(session):
    """POST /post с multipart: имя файла попадает в files, обычные поля — в form."""
    files = {"report": ("report.txt", b"line1\nline2", "text/plain")}

    response = session.post(
        POST_URL, files=files, data={"comment": "upload"}, timeout=TIMEOUT
    )

    assert response.status_code == 200
    body = response.json()
    assert "report.txt" in body["files"]
    assert body["form"]["comment"] == "upload"
    assert body["headers"]["content-type"].startswith("multipart/form-data; boundary=")


def test_post_url_accepts_query_params_too(session):
    """POST /post: квери-параметры и тело отражаются одновременно и независимо."""
    response = session.post(
        POST_URL,
        params={"source": "ci"},
        json={"value": 1},
        timeout=TIMEOUT,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["args"] == {"source": "ci"}
    assert body["json"] == {"value": 1}
    assert body["url"] == f"{POST_URL}?source=ci"


@pytest.mark.parametrize(
    "method,url",
    [
        ("POST", GET_URL),
        ("PUT", GET_URL),
        ("DELETE", GET_URL),
        ("GET", POST_URL),
        ("PATCH", POST_URL),
    ],
)
def test_wrong_method_for_endpoint_returns_404(session, method, url):
    """Каждый эндпоинт отвечает только на свой метод, остальные дают 404."""
    response = session.request(method, url, timeout=TIMEOUT)

    assert response.status_code == 404


def test_head_get_returns_headers_without_body(session):
    """HEAD /get: статус 200, тело пустое, Content-Type сохраняется."""
    response = session.head(GET_URL, timeout=TIMEOUT)

    assert response.status_code == 200
    assert response.text == ""
    assert response.headers["Content-Type"].startswith("application/json")
