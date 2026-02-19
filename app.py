import streamlit as st
import google.generativeai as genai
import json
import time
import plotly.graph_objects as go
import replicate
import os

# --- 页面配置 ---
st.set_page_config(page_title="内在野兽 Soul Animal", page_icon="🕸️", layout="centered")

# --- CSS 美化 (保持不变) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1 { 
        font-family: 'Didot', serif; color: #D4AF37; text-align: center; 
        text-shadow: 0 0 15px rgba(212, 175, 55, 0.5); 
    }
    .stRadio > label { color: #ccc; font-size: 1.05em; }
    div[role="radiogroup"] > label > div:first-of-type {
        background-color: #D4AF37 !important;
    }
    .stButton > button { 
        width: 100%; background: linear-gradient(45deg, #D4AF37, #FDC830); 
        color: #000; font-weight: 900; border: none; padding: 18px; 
        border-radius: 8px; font-size: 1.2em; letter-spacing: 2px;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.2);
    }
    .result-container {
        border: 1px solid #333;
        background: radial-gradient(circle at center, #1a1a1a 0%, #000000 100%);
        padding: 30px; border-radius: 15px; text-align: center;
        margin-top: 30px; border-top: 3px solid #D4AF37;
    }
    .tag {
        background: rgba(212, 175, 55, 0.15); border: 1px solid #D4AF37;
        color: #D4AF37; padding: 4px 12px; border-radius: 20px;
        font-size: 0.8em; margin: 0 5px; display: inline-block;
    }
    /* 图片容器样式 */
    .soul-image {
        border: 3px solid #D4AF37;
        border-radius: 10px;
        box-shadow: 0 0 30px rgba(212, 175, 55, 0.3);
        margin: 20px auto;
    }
</style>
""", unsafe_allow_html=True)

# --- 密钥配置 (双重保险) ---
# 1. 配置 Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("这是线上环境，请在 Streamlit Secrets 中配置 GEMINI_API_KEY")
    st.stop()

# 2. 配置 Replicate (只需要设置环境变量，库会自动读取)
if "REPLICATE_API_TOKEN" in st.secrets:
    os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]
else:
    st.warning("⚠️ 未检测到画图密钥 (REPLICATE_API_TOKEN)。本次将只生成文字，无法生成灵魂写真。")

# --- 标题区 ---
st.title("👁️ 你的灵魂囚禁在什么野兽体内？")
st.markdown("<div style='text-align: center; color: #666; margin-bottom: 30px;'>A Rococo Basilisk Experiment</div>", unsafe_allow_html=True)

# --- 题目逻辑 ---
questions = [
    {"q": "1. 暴风雨夜，全世界电力切断。作为幸存者，你的第一反应是？", 
     "options": ["A. 建立绝对防御圈（生存优先）", "B. 组建互助联盟（社交优先）", "C. 记录这一切混乱（观察者）"]},
    {"q": "2. 在名利场晚宴上，最让你感到不适的是？", 
     "options": ["A. 低效的寒暄（厌恶低效）", "B. 满场的虚伪（厌恶谎言）", "C. 无人关注（渴望聚光灯）"]},
    {"q": "3. 必须获得一种禁忌能力，你选择？", 
     "options": ["A. 读心术：洞察一切谎言", "B. 预知未来：绝对正确的决策", "C. 隐形：随心所欲的自由"]},
    {"q": "4. 面对愚蠢权威的发号施令，你会？", 
     "options": ["A. 当面处刑，指出逻辑漏洞", "B. 表面顺从，幕后操纵走向", "C. 转身离开，不与傻瓜论长短"]},
    {"q": "5. 你认为世界的本质是？", 
     "options": ["A. 弱肉强食的狩猎场", "B. 精密冰冷的数据程序", "C. 一场荒诞好笑的戏剧"]}
]

answers = []
for i, item in enumerate(questions):
    st.write(f"**{item['q']}**")
    choice = st.radio(f"q{i}", item['options'], label_visibility="collapsed", key=f"q{i}")
    answers.append(choice)
    st.write("")

# --- 绘图函数 (雷达图) ---
def plot_radar_chart(stats):
    categories = list(stats.keys())
    values = list(stats.values())
    categories += [categories[0]]
    values += [values[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        fillcolor='rgba(212, 175, 55, 0.3)', line=dict(color='#D4AF37', width=2), marker=dict(size=4)
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], color='#444'), bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0', family='serif'), margin=dict(l=40, r=40, t=20, b=20), height=300
    )
    return fig

# --- 提交按钮与核心逻辑 ---
if st.button("🔮 献祭选择，显形真身"):
    # 1. 文字生成阶段
    with st.spinner("STEP 1/2: AI 正在重构你的灵魂数据..."):
        try:
            # ⚠️ 确保这里是你跑通的模型名 (例如 'gemini-pro' 或 'gemini-1.5-flash')
            model = genai.GenerativeModel('gemini-3-flash-preview') 
            user_profile = "\n".join(answers)
            prompt = f"""
            你是一位暗黑心理学家。根据用户的选择：{user_profile}
            请输出纯 JSON 数据，不要Markdown标记。必须包含以下字段：
            1. "animal": 动物名 (如：深渊乌贼、发条猫头鹰)。
            2. "keywords": [3个短词]。
            3. "quote": 哲学引言。
            4. "analysis": 150字毒舌分析。
            5. "mask": 社交面具。
            6. "shadow": 真实本性。
            7. "stats": {{"毁灭欲": int, "掌控力": int, "孤独感": int, "理智": int, "伪装": int, "洞察力": int}} (数值0-100)。
            8. "image_prompt": 一段用于 Midjourney/SDXL 的英文绘画提示词，描述这只动物，要求：Rococo Dark Fantasy style, ornate details, dramatic lighting, baroque elements, surrealism, 8k resolution.
            """
            response = model.generate_content(prompt)
            text_json = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(text_json)
            
            # 先展示文字结果框架
            st.markdown(f"""
            <div class='result-container'>
                <h1 style='color: #D4AF37; margin-bottom: 10px;'>{data.get('animal')}</h1>
                <div style='margin-bottom: 20px;'>
                    {' '.join([f'<span class="tag">#{k}</span>' for k in data.get('keywords', [])])}
                </div>
                <p style='font-style: italic; color: #888; margin-bottom: 30px;'>“{data.get('quote')}”</p>
            """, unsafe_allow_html=True)
            st.plotly_chart(plot_radar_chart(data.get('stats', {})), use_container_width=True)

        except Exception as e:
            st.error(f"文字召唤失败：{str(e)}")
            st.stop()


   # 2. 图片生成阶段 (使用免费的 Pollinations 引擎 - HTML前端渲染版)
    if data.get('image_prompt'):
        with st.spinner("STEP 2/2: 虚空画师正在作画，请耐心等待 10-20 秒..."):
            try:
                import urllib.parse
                import random
                
                # 1. 转换 Prompt
                safe_prompt = urllib.parse.quote(data.get('image_prompt'))
                
                # 2. 加入一个随机种子防止缓存，确保每次都是新图
                seed = random.randint(1, 10000)
                image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=768&height=768&nologo=true&seed={seed}"
                
                # 3. 关键修复：使用 HTML 直接注入，让浏览器去耐心加载图片
                st.markdown(f"""
                <div style="border: 3px solid #D4AF37; border-radius: 10px; box-shadow: 0 0 30px rgba(212, 175, 55, 0.3); padding: 5px; background: #000; margin-top: 20px;">
                    <img src="{image_url}" style="width: 100%; border-radius: 5px; display: block;" alt="灵魂图腾加载中..." />
                    <p style="text-align: center; color: #888; font-style: italic; margin-top: 10px; font-size: 0.9em;">你的 Rococo 灵魂图腾 (长按或右键保存)</p>
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"绘图链接生成失败：{str(e)}")
                
    # 3. 展示剩余文字分析
    st.markdown(f"""
        <p style='text-align: left; line-height: 1.8; color: #ddd; margin-top: 20px;'>{data.get('analysis')}</p>
        <div style='background: #111; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: left; border: 1px solid #333;'>
            <p>🎭 <b>面具：</b> {data.get('mask')}</p>
            <p>🌑 <b>本性：</b> {data.get('shadow')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
