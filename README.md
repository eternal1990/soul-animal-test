# Soul Animal Test

一个 Streamlit 灵魂图腾测试原型。用户完成 5 道选择题后，应用会调用可选文本模型生成结构化心理侧写，并在配置视觉模型后生成图腾图片或视频 prompt。

## 功能

- 分页式 5 题测试流程
- Gemini / OpenAI GPT / xAI Grok 生成动物名、关键词、引言、侧写、面具/内核和雷达图分数
- SiliconFlow FLUX 图片生成，可选启用
- Seedance 视频 prompt 输出，可复制到支持 Seedance 的视频生成入口
- 对 AI 返回 JSON 做 schema validation
- 对 AI 文本输出做 HTML escape，降低 `unsafe_allow_html` 渲染风险
- SiliconFlow 请求包含 timeout、HTTP status 和响应结构校验

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Secrets 配置

复制示例文件后填入本地密钥：

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

`.streamlit/secrets.toml`：

```toml
GEMINI_API_KEY = "your-gemini-api-key"
OPENAI_API_KEY = "your-openai-api-key"
XAI_API_KEY = "your-xai-api-key"
SILICONFLOW_API_KEY = "your-siliconflow-api-key"
```

至少配置一个文本模型 key。`SILICONFLOW_API_KEY` 可选；不配置时可选择 Seedance prompt-only 输出，或只生成文字结果。

不要把真实 `.streamlit/secrets.toml` 提交到 Git。

## 验证

```bash
python3 -m py_compile app.py soul-animal-dark soul_animal_helpers.py test_app.py
python3 -m unittest test_app.py
```

## 模型选择

| 用途 | 选项 | Secrets | 说明 |
| --- | --- | --- | --- |
| 文本分析 | Gemini 2.5 Flash | `GEMINI_API_KEY` | 默认选项，沿用原实现 |
| 文本分析 | OpenAI GPT-5.5 | `OPENAI_API_KEY` | 高质量侧写和 JSON 生成 |
| 文本分析 | OpenAI GPT-5.4 mini | `OPENAI_API_KEY` | 成本和速度优先 |
| 文本分析 | xAI Grok 4.3 | `XAI_API_KEY` | Grok Chat API 选项 |
| 图片生成 | SiliconFlow FLUX.1 schnell | `SILICONFLOW_API_KEY` | 直接生成方图 |
| 视频生成 | Seedance prompt-only | 无 | Seedance 是视频模型；当前先输出可复制 prompt，不硬编码第三方 API endpoint |

## 文件说明

- `app.py`：当前空灵/治愈方向的主应用
- `soul-animal-dark`：暗黑方向实验脚本，保留为独立方向
- `requirements.txt`：运行依赖
- `.streamlit/secrets.toml.example`：本地 secrets 示例，不包含真实密钥
