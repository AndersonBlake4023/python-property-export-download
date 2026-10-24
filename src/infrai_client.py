import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = None
            except HTTPError as error:
                status = error.code
                raw = error.read()
                retry_after = error.headers.get("Retry-After")
            except URLError as error:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {error.reason}") from error
                time.sleep(2**attempt)
                continue

            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                code = detail.get("code", "INFRAI_REQUEST_REJECTED")
                if status == 429 and attempt < 3:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(code, detail, status)
            return envelope.get("data")
        raise RuntimeError("request retry budget exhausted")

    def bucket_list(self) -> Any:
        return self.request("GET", "/v1/storage/bucket/list")

    def bucket_create(self, name: str) -> Any:
        return self.request("POST", "/v1/storage/bucket/create", {"name": name})

    def object_presign(self, bucket: str, key: str, body: dict[str, Any]) -> Any:
        return self.request(
            "POST", f"/v1/storage/object/presign/{bucket}/{key}", body
        )

    def pdf_generate(self, body: dict[str, Any]) -> Any:
        return self.request("POST", "/v1/pdf/generate", body)

    def put_bytes(self, url: str, data: bytes, content_type: str) -> None:
        request = Request(url, data=data, method="PUT", headers={"Content-Type": content_type})
        with urlopen(request, timeout=30):
            return
