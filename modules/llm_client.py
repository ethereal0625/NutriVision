"""llm_client.py - Provider-agnostic chat completion for text models."""
from typing import Any

from config import API_ENDPOINTS, LIMITS, MODELS
from modules.common import load_api_key, parse_json, retry


def chat_completion(prompt: str, model: str, temperature: float = 0.3) -> Any:
    """Call a text model via DashScope / Zhipu / Doubao and return parsed JSON."""
    info = MODELS.get(model, {"provider": "dashscope", "type": "text"})
    provider = info["provider"]

    def call():
        if provider == "dashscope":
            import dashscope
            from dashscope import Generation
            dashscope.api_key = load_api_key("dashscope")
            resp = Generation.call(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                result_format="message",
            )
            if resp.status_code != 200:
                raise RuntimeError(f"status={resp.status_code} code={resp.code} msg={resp.message}")
            return parse_json(resp.output.choices[0].message.content)

        import requests
        api_key = load_api_key(provider)
        actual_model = info.get("endpoint_id", model)
        resp = requests.post(
            API_ENDPOINTS[provider],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": actual_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            },
            timeout=LIMITS["api_timeout_seconds"],
        )
        if resp.status_code != 200:
            raise RuntimeError(f"{provider} status={resp.status_code} body={resp.text[:200]}")
        return parse_json(resp.json()["choices"][0]["message"]["content"])

    return retry(call)


def pick_text_model(has_dashscope_key: bool) -> str:
    """Paid Qwen when the user brought their own key, else free Zhipu GLM-4-Flash."""
    return "qwen-plus" if has_dashscope_key else "glm-4-flash"
