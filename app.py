import streamlit as st
import google.generativeai as genai
import json
import plotly.graph_objects as go
import requests

# --- 页面配置 ---
st.set_page_config(page_title="灵魂潜行", page_icon="✨", layout="centered")

# --- 移动端优化 CSS ---
st.markdown("""
<style>
    /* 全局背景与字体 - 偏向深邃空灵 */
    .stApp { background-color: #080b12; color: #e6e9f0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    h1, h2, h3 { color: #E5C07B; text-align: center; font-weight: 300; letter-spacing: 2px; }
    
    /* 进度条样式 */
    .stProgress > div > div > div > div { background-color: #E5C07B; }
    
    /* 单选题优化：扩大点击热区，适合手机盲按 */
    .stRadio > label { font-size: 1.1rem !important; color: #abb2bf; margin-bottom: 10px; }
    div[role="radiogroup"] > label {
        padding: 15px; 
        background: rgba(255,255,255,0.03); 
        border-radius: 10px; 
        border: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 10px;
    }
    div[role="radiogroup"] > label > div:first-of-type { background-color: #E5C07B !important; }

    /* 按钮样式：大圆角，防误触 */
    .stButton > button { 
        width: 100%; background: linear-gradient(135deg, #E5C07B, #D4AF37); 
        color: #1e1e1e; font-weight: bold; border: none; padding: 15px; 
        border-radius: 25px; font-size: 1.1em; letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(229, 192, 123, 0.2);
        margin-top: 20px;
    }
    
    /* 结果卡片 */
    .result-container {
        background: linear-gradient(180deg, rgba(30,34,42,0.8) 0%, rgba(15,17,21,0.9) 100%);
        padding: 25px; border-radius: 20px; text-align: center;
        margin-top: 20px; border: 1px solid rgba(229,192,123,0.2);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .tag {
        background: rgba(229, 192, 123, 0.1); border: 1px solid #E5C07B;
        color: #E5C07B; padding: 5px 15px; border-radius: 20px;
        font-size: 0.85rem; margin: 4px; display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- 状态管理 (用于分页) ---
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# --- 密钥配置 ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("请在 Streamlit Secrets 中配置 GEMINI_API_KEY")
    st.stop()

# --- 题库 ---
questions = [
    {"id": "q1", "q": "1. 暴风雨夜，全世界电力切断。作为幸存者，你的第一反应是？", 
     "options": ["A. 建立绝对防御圈（生存优先）", "B. 组建互助联盟（社交优先）", "C. 记录这一切混乱（观察者）"]},
    {"id": "q2", "q": "2. 在名利场晚宴上，最让你感到不适的是？", 
     "options": ["A. 低效的寒暄与客套", "B. 满场的虚伪与面具", "C. 无人关注到你的存在"]},
    {"id": "q3", "q": "3. 如果必须获得一种能力，你会选择？", 
     "options": ["A. 读心术：洞察一切谎言", "B. 预知未来：掌握绝对因果", "C. 隐形：获得纯粹的自由"]},
    {"id": "q4", "q": "4. 面对愚蠢权威的发号施令，你的本能反应是？", 
     "options": ["A. 当面指出逻辑漏洞", "B. 表面顺从，幕后按自己方式办", "C. 转身离开，不浪费时间"]},
    {"id": "q5", "q": "5. 你认为这个世界的底层运行逻辑更像是？", 
     "options": ["A. 弱肉强食的黑暗森林", "B. 精密冰冷的因果程序", "C. 一场没有意义但有趣的戏剧"]}
]

# --- 绘图函数 ---
def plot_radar_chart(stats):
    categories = list(stats.keys())
    values = list(stats.values())
    categories += [categories[0]]
    values += [values[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill='toself',
        fillcolor='rgba(229, 192, 123, 0.2)', line=dict(color='#E5C07B', width=2), marker=dict(size=4)
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 100]), bgcolor='rgba(0,0,0,0)'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#abb2bf', size=14), margin=dict(l=30, r=30, t=20, b=20), height=280
    )
    return fig

# --- 交互界面 ---
st.title("✨ 灵魂显影测试")
st.markdown("<p style='text-align: center; color: #7f848e; font-size: 0.9rem; margin-bottom: 20px;'>测一测你内在的真实图腾</p>", unsafe_allow_html=True)

# 进度条
# 进度条 (使用 min 函数，确保进度最大不会超过 1.0 即 100%)
progress_bar = st.progress(min(st.session_state.page / 3, 1.0))

# ================= 第 1 页 (Q1, Q2) =================
if st.session_state.page == 1:
    st.write("### Part 1: 本能与社交")
    ans1 = st.radio(questions[0]['q'], questions[0]['options'], index=None, key="r1")
    ans2 = st.radio(questions[1]['q'], questions[1]['options'], index=None, key="r2")
    
    if st.button("下一页 ➜"):
        if ans1 and ans2:
            st.session_state.answers['q1'] = ans1
            st.session_state.answers['q2'] = ans2
            st.session_state.page = 2
            st.rerun()
        else:
            st.warning("请完成本页所有直觉选择。")

# ================= 第 2 页 (Q3, Q4) =================
elif st.session_state.page == 2:
    st.write("### Part 2: 欲望与边界")
    ans3 = st.radio(questions[2]['q'], questions[2]['options'], index=None, key="r3")
    ans4 = st.radio(questions[3]['q'], questions[3]['options'], index=None, key="r4")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ 返回"):
            st.session_state.page = 1
            st.rerun()
    with col2:
        if st.button("下一页 ➜"):
            if ans3 and ans4:
                st.session_state.answers['q3'] = ans3
                st.session_state.answers['q4'] = ans4
                st.session_state.page = 3
                st.rerun()
            else:
                st.warning("请完成本页所有直觉选择。")

# ================= 第 3 页 (Q5 + 结果生成) =================
elif st.session_state.page == 3:
    st.write("### Part 3: 世界观")
    ans5 = st.radio(questions[4]['q'], questions[4]['options'], index=None, key="r5")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ 返回"):
            st.session_state.page = 2
            st.rerun()
            
    with col2:
        if st.button("🔮 生成图腾"):
            if not ans5:
                st.warning("请完成最后一题。")
            else:
                st.session_state.answers['q5'] = ans5
                st.session_state.page = 4 # 跳转到结果页
                st.rerun()

# ================= 结果加载页 =================
elif st.session_state.page == 4:
    with st.spinner("正在通过星界连接你的潜意识..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash') 
            user_profile = "\n".join(list(st.session_state.answers.values()))
            
            # --- Prompt 调整：从暗黑转为空灵/智性/治愈 ---
            prompt = f"""
            你是一位洞察人心的神秘学导师。根据用户的选择：{user_profile}
            请输出纯 JSON 数据，不要Markdown标记。必须包含：
            1. "animal": 动物名 (如：星光雪豹、水晶琉璃鹿、机械智者猫头鹰，名字要带有神性或空灵感)。
            2. "keywords": [3个短词，体现智性、空灵或力量]。
            3. "quote": 一句极具诗意与哲理的引言。
            4. "analysis": 150字侧写。犀利地指出他的孤独与防备，但最终给予肯定和治愈（例如：你的冷漠其实是保护内心的火种）。
            5. "mask": 社交面具（他如何应对外界）。
            6. "shadow": 真实本性（他内心的柔软或高傲）。
            7. "stats": {{"独立性": int, "洞察力": int, "边界感": int, "精神力": int, "共情力": int, "掌控欲": int}} (数值0-100)。
            8. "image_prompt": 一段用于 FLUX 模型的英文提示词，描述这只动物。风格要求：Ethereal fantasy, majestic, highly detailed, luminous, glowing crystal elements, cinematic lighting, Studio Ghibli meets Tarot card art, masterpiece, 8k.
            """
            response = model.generate_content(prompt)
            text_json = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(text_json)
            
            # 展示文字框架
            st.markdown(f"""
            <div class='result-container'>
                <h1 style='color: #E5C07B; margin-bottom: 5px;'>{data.get('animal')}</h1>
                <p style='font-style: italic; color: #abb2bf; margin-bottom: 20px;'>“{data.get('quote')}”</p>
                <div style='margin-bottom: 20px;'>
                    {' '.join([f'<span class="tag">#{k}</span>' for k in data.get('keywords', [])])}
                </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(plot_radar_chart(data.get('stats', {})), use_container_width=True)

            # 调用硅基流动生成图片
            if "SILICONFLOW_API_KEY" in st.secrets and data.get('image_prompt'):
                url = "https://api.siliconflow.cn/v1/images/generations"
                headers = {"Authorization": f"Bearer {st.secrets['SILICONFLOW_API_KEY']}", "Content-Type": "application/json"}
                # 强化空灵神圣的画风
                enhanced_prompt = f"Masterpiece, breathtaking ethereal fantasy art, majestic, luminous, {data.get('image_prompt')}"
                payload = {"model": "black-forest-labs/FLUX.1-schnell", "prompt": enhanced_prompt, "image_size": "1024x1024", "batch_size": 1}
                
                res = requests.post(url, json=payload, headers=headers)
                res_data = res.json()
                
                if "images" in res_data:
                    st.image(res_data["images"][0]["url"], caption="你的灵魂图腾 (长按保存)", use_container_width=True)
                    st.markdown("""<style>.stImage > img {border: 2px solid #E5C07B; border-radius: 15px;}</style>""", unsafe_allow_html=True)
            
            # 深度分析
            st.markdown(f"""
                <p style='text-align: left; line-height: 1.8; color: #d7dae0; margin-top: 25px; font-size: 1.05rem;'>{data.get('analysis')}</p>
                <div style='background: rgba(255,255,255,0.03); padding: 20px; border-radius: 12px; margin-top: 20px; text-align: left;'>
                    <p style='color: #abb2bf;'>🛡️ <b>表象面具：</b> <span style='color: #e6e9f0;'>{data.get('mask')}</span></p>
                    <p style='color: #abb2bf;'>✨ <b>真实内核：</b> <span style='color: #e6e9f0;'>{data.get('shadow')}</span></p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 重新测试按钮
            if st.button("↻ 重新探索"):
                st.session_state.page = 1
                st.session_state.answers = {}
                st.rerun()

        except Exception as e:
            st.error(f"星界连接波动，请重试：{str(e)}")
            if st.button("返回首页"):
                st.session_state.page = 1
                st.rerun()
