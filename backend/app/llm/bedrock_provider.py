"""AWS Bedrock LLM provider (Claude vision via invoke_model)."""

from __future__ import annotations

import base64
import json

from ..config import settings


class BedrockError(RuntimeError):
    pass


class BedrockProvider:
    def __init__(
        self,
        model_id: str | None = None,
        region: str | None = None,
        max_tokens: int = 2048,
    ) -> None:
        self._model_id = model_id or settings.bedrock_model_id
        self._region = region or settings.aws_region
        self._max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client("bedrock-runtime", region_name=self._region)
        return self._client

    def generate(self, prompt: str, images: list[bytes] | None = None) -> str:
        content: list[dict] = []
        for img in images or []:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.b64encode(img).decode("ascii"),
                    },
                }
            )
        content.append({"type": "text", "text": prompt})

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": content}],
        }

        try:
            client = self._get_client()
            resp = client.invoke_model(
                modelId=self._model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
        except Exception as exc:  # noqa: BLE001
            raise BedrockError(f"Bedrock invoke_model failed: {exc}") from exc

        payload = json.loads(resp["body"].read())
        parts = payload.get("content", [])
        texts = [p.get("text", "") for p in parts if p.get("type") == "text"]
        return "".join(texts).strip()
