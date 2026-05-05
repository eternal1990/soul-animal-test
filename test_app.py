import unittest
from unittest.mock import Mock, patch

import requests

from soul_animal_helpers import (
    TEXT_MODEL_OPTIONS,
    build_seedance_video_prompt,
    extract_json_payload,
    escape_profile_for_html,
    generate_openai_compatible_chat_text,
    generate_siliconflow_image_url,
    get_text_model_option,
    validate_soul_profile,
)


VALID_PROFILE = {
    "animal": "星光雪豹",
    "keywords": ["洞察", "边界", "柔软"],
    "quote": "在黑夜里保持清醒。",
    "analysis": "你看似冷静，其实是在保护内心的火种。",
    "mask": "礼貌而疏离",
    "shadow": "高傲也柔软",
    "stats": {"独立性": 90, "洞察力": 88, "边界感": 95},
    "image_prompt": "A luminous snow leopard",
}


class SoulAnimalHelpersTest(unittest.TestCase):
    def test_text_model_options_include_gemini_gpt_and_grok(self):
        self.assertEqual(TEXT_MODEL_OPTIONS["gemini_2_5_flash"]["secret_name"], "GEMINI_API_KEY")
        self.assertEqual(TEXT_MODEL_OPTIONS["openai_gpt_5_5"]["model"], "gpt-5.5")
        self.assertEqual(TEXT_MODEL_OPTIONS["openai_gpt_5_5"]["secret_name"], "OPENAI_API_KEY")
        self.assertEqual(TEXT_MODEL_OPTIONS["xai_grok_4_3"]["model"], "grok-4.3")
        self.assertEqual(TEXT_MODEL_OPTIONS["xai_grok_4_3"]["base_url"], "https://api.x.ai/v1")

    def test_get_text_model_option_rejects_unknown_id(self):
        with self.assertRaisesRegex(ValueError, "未知模型"):
            get_text_model_option("missing")

    def test_extract_json_payload_rejects_extra_text(self):
        with self.assertRaisesRegex(ValueError, "额外内容"):
            extract_json_payload('{"animal": "雪豹"} trailing')

    def test_validate_soul_profile_requires_expected_schema(self):
        profile = validate_soul_profile(VALID_PROFILE)

        self.assertEqual(profile["animal"], "星光雪豹")
        self.assertEqual(profile["keywords"], ["洞察", "边界", "柔软"])
        self.assertEqual(profile["stats"]["洞察力"], 88)

    def test_validate_soul_profile_rejects_out_of_range_stats(self):
        payload = dict(VALID_PROFILE)
        payload["stats"] = {"独立性": 101}

        with self.assertRaisesRegex(ValueError, "0-100"):
            validate_soul_profile(payload)

    def test_escape_profile_for_html_escapes_llm_text(self):
        payload = dict(VALID_PROFILE)
        payload["animal"] = "<script>alert(1)</script>"
        payload["keywords"] = ['"><img src=x onerror=alert(1)>', "边界", "柔软"]

        escaped = escape_profile_for_html(validate_soul_profile(payload))

        self.assertEqual(escaped["animal"], "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertIn("&quot;&gt;&lt;img", escaped["keywords"][0])

    @patch("soul_animal_helpers.requests.post")
    def test_generate_siliconflow_image_url_uses_timeout_and_validates_response(self, post):
        response = Mock()
        response.json.return_value = {"images": [{"url": "https://example.com/image.png"}]}
        response.raise_for_status.return_value = None
        post.return_value = response

        image_url = generate_siliconflow_image_url("prompt", "secret", timeout=5)

        self.assertEqual(image_url, "https://example.com/image.png")
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["timeout"], 5)

    @patch("soul_animal_helpers.requests.post", side_effect=requests.Timeout())
    def test_generate_siliconflow_image_url_reports_timeout(self, post):
        with self.assertRaisesRegex(RuntimeError, "超时"):
            generate_siliconflow_image_url("prompt", "secret", timeout=5)

    @patch("soul_animal_helpers.requests.post")
    def test_generate_openai_compatible_chat_text_posts_to_chat_completions(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": '{"animal": "星光雪豹"}'}}]}
        response.raise_for_status.return_value = None
        post.return_value = response

        text = generate_openai_compatible_chat_text(
            "https://api.openai.com/v1",
            "gpt-5.5",
            "secret",
            "prompt",
            timeout=7,
        )

        self.assertEqual(text, '{"animal": "星光雪豹"}')
        self.assertEqual(post.call_args.args[0], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "gpt-5.5")
        self.assertEqual(post.call_args.kwargs["timeout"], 7)

    @patch("soul_animal_helpers.requests.post")
    def test_generate_openai_compatible_chat_text_validates_choice_content(self, post):
        response = Mock()
        response.json.return_value = {"choices": []}
        response.raise_for_status.return_value = None
        post.return_value = response

        with self.assertRaisesRegex(RuntimeError, "文本内容"):
            generate_openai_compatible_chat_text("https://api.x.ai/v1", "grok-4.3", "secret", "prompt")

    def test_build_seedance_video_prompt_uses_profile_details(self):
        prompt = build_seedance_video_prompt(VALID_PROFILE)

        self.assertIn("星光雪豹", prompt)
        self.assertIn("A luminous snow leopard", prompt)
        self.assertIn("cinematic", prompt)


if __name__ == "__main__":
    unittest.main()
