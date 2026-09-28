import json

import requests


def response(status=200, data=None, headers=None):
    result = requests.Response()
    result.status_code = status
    result.headers.update({"Content-Type": "application/json"})
    result.headers.update(headers or {})
    result._content_consumed = True
    result._content = json.dumps({} if data is None else data).encode()
    return result
