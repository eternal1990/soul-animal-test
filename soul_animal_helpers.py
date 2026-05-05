import html
import json

import requests

SILICONFLOW_IMAGE_URL = "https://api.siliconflow.cn/v1/images/generations"
SILICONFLOW_MODEL = "black-forest-labs/FLUX.1-schnell"
SILICONFLOW_TIMEOUT_SECONDS = 30
OPENAI_COMPATIBLE_TIMEOUT_SECONDS = 60

TEXT_MODEL_OPTIONS = {
    "gemini_2_5_flash": {
        "label": "Gemini 2.5 Flash",
        "provider": "gemini",
        "model": "models/gemini-2.5-flash",
        "secret_name": "GEMINI_API_KEY",
        "base_url": None,
    },
    "openai_gpt_5_5": {
        "label": "OpenAI GPT-5.5",
        "provider": "openai_compatible",
        "model": "gpt-5.5",
        "secret_name": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
    },
    "openai_gpt_5_4_mini": {
        "label": "OpenAI GPT-5.4 mini",
        "provider": "openai_compatible",
        "model": "gpt-5.4-mini",
        "secret_name": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
    },
    "xai_grok_4_3": {
        "label": "xAI Grok 4.3",
        "provider": "openai_compatible",
        "model": "grok-4.3",
        "secret_name": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
    },
}

DEFAULT_TEXT_MODEL_ID = "gemini_2_5_flash"


def get_text_model_option(model_id):
    option = TEXT_MODEL_OPTIONS.get(model_id)
    if option is None:
        raise ValueError(f"未知模型：{model_id}")
    return option


def extract_json_payload(raw_text):
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    decoder = json.JSONDecoder()
    try:
        data, end_index = decoder.raw_decode(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("AI 返回结果不是合法 JSON，请重试。") from exc

    if cleaned[end_index:].strip():
        raise ValueError("AI 返回结果包含 JSON 之外的额外内容，请重试。")

    return data


def validate_soul_profile(data):
    required_text_fields = ["animal", "quote", "analysis", "mask", "shadow", "image_prompt"]
    required_keys = set(required_text_fields + ["keywords", "stats"])
    missing_keys = sorted(required_keys - set(data.keys())) if isinstance(data, dict) else sorted(required_keys)
    if missing_keys:
        raise ValueError(f"AI 返回结果缺少字段：{', '.join(missing_keys)}")

    normalized = {}
    for field in required_text_fields:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI 返回字段 {field} 必须是非空文本。")
        normalized[field] = value.strip()

    keywords = data.get("keywords")
    if not isinstance(keywords, list) or len(keywords) != 3:
        raise ValueError("AI 返回字段 keywords 必须是 3 个短词。")
    normalized["keywords"] = []
    for keyword in keywords:
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("AI 返回字段 keywords 必须只包含非空文本。")
        normalized["keywords"].append(keyword.strip())

    stats = data.get("stats")
    if not isinstance(stats, dict) or not stats:
        raise ValueError("AI 返回字段 stats 必须是非空对象。")
    normalized["stats"] = {}
    for key, value in stats.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("AI 返回字段 stats 的维度名必须是非空文本。")
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            raise ValueError("AI 返回字段 stats 的数值必须是 0-100 的整数。")
        normalized["stats"][key.strip()] = value

    return normalized


def escape_profile_for_html(data):
    escaped = {}
    for key in ["animal", "quote", "analysis", "mask", "shadow"]:
        escaped[key] = html.escape(data[key], quote=True)
    escaped["keywords"] = [html.escape(keyword, quote=True) for keyword in data["keywords"]]
    return escaped


def generate_openai_compatible_chat_text(base_url, model, api_key, prompt, timeout=OPENAI_COMPATIBLE_TIMEOUT_SECONDS):
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You generate strict JSON only. Do not include Markdown fences or extra prose.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        response_data = response.json()
    except requests.Timeout as exc:
        raise RuntimeError("文本模型请求超时，请稍后重试。") from exc
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        raise RuntimeError(f"文本模型请求失败，HTTP 状态码：{status_code}") from exc
    except requests.RequestException as exc:
        raise RuntimeError("文本模型网络请求失败，请稍后重试。") from exc
    except ValueError as exc:
        raise RuntimeError("文本模型返回结果不是合法 JSON。") from exc

    choices = response_data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("文本模型返回结果缺少文本内容。")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("文本模型返回结果缺少文本内容。")

    return content.strip()


def generate_siliconflow_image_url(image_prompt, api_key, timeout=SILICONFLOW_TIMEOUT_SECONDS):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    enhanced_prompt = f"Masterpiece, breathtaking ethereal fantasy art, majestic, luminous, {image_prompt}"
    payload = {
        "model": SILICONFLOW_MODEL,
        "prompt": enhanced_prompt,
        "image_size": "1024x1024",
        "batch_size": 1,
    }

    try:
        response = requests.post(SILICONFLOW_IMAGE_URL, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        response_data = response.json()
    except requests.Timeout as exc:
        raise RuntimeError("SiliconFlow 图片生成请求超时，请稍后重试。") from exc
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        raise RuntimeError(f"SiliconFlow 图片生成失败，HTTP 状态码：{status_code}") from exc
    except requests.RequestException as exc:
        raise RuntimeError("SiliconFlow 图片生成网络请求失败，请稍后重试。") from exc
    except ValueError as exc:
        raise RuntimeError("SiliconFlow 返回结果不是合法 JSON。") from exc

    images = response_data.get("images")
    if not isinstance(images, list) or not images:
        raise RuntimeError("SiliconFlow 返回结果缺少图片链接，可能是余额不足或安全审核未通过。")

    image_url = images[0].get("url") if isinstance(images[0], dict) else None
    if not isinstance(image_url, str) or not image_url.startswith(("http://", "https://")):
        raise RuntimeError("SiliconFlow 返回的图片链接格式不正确。")

    return image_url


def build_seedance_video_prompt(data):
    keywords = ", ".join(data["keywords"])
    return (
        f"Seedance video prompt: {data['animal']}. {data['image_prompt']}. "
        f"Keywords: {keywords}. Create a 5-second cinematic slow reveal, ethereal fantasy tone, "
        "stable subject identity, soft camera push-in, luminous particles, coherent motion, no text overlay."
    )
