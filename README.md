# postman-echo-tests

Автотесты публичного REST-сервиса [postman-echo.com](https://postman-echo.com)
на `requests` + `pytest`. Проверяется поведение эндпоинтов
`GET /get` и `POST /post`, предварительно изученное вручную в Postman.

## Что покрыто

| Тест | Что проверяет |
| --- | --- |
| `test_get_query_params_are_echoed` | `GET /get` возвращает квери-параметры в `args`, повторяющийся параметр — списком |
| `test_get_echoes_custom_headers` | пользовательские заголовки возвращаются в `headers` в нижнем регистре |
| `test_post_form_urlencoded` | тело `application/x-www-form-urlencoded` попадает в `form`, `data` пустая |
| `test_post_json_body` | JSON-тело возвращается в `json` и `data`, `Content-Length` совпадает |
| `test_post_raw_text_body` | тело `text/plain` кладётся в `data` строкой, `json = null` |
| `test_post_multipart_file_upload` | multipart: файл в `files`, обычное поле в `form` |
| `test_post_url_accepts_query_params_too` | `POST /post` одновременно отражает и квери-параметры, и тело |
| `test_wrong_method_for_endpoint_returns_404` | каждый эндпоинт отвечает только на свой метод, остальные — `404` (5 кейсов) |
| `test_head_get_returns_headers_without_body` | `HEAD /get` — `200` с пустым телом |

Итого 13 тестов (9 функций, одна параметризована на 5 кейсов).

## Запуск локально

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

Тестам нужен интернет — они ходят в реальный сервис.

## CI

GitHub Actions — [`.github/workflows/tests.yml`](.github/workflows/tests.yml):
прогон `pytest -v` на каждый push в `main`, на каждый pull request и по кнопке
(`workflow_dispatch`).
