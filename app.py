import streamlit as st
import requests
import json

# ==========================================
# 核心 API 调用函数 (适配中转站与页面输入的 Key)
# ==========================================
def call_ai_api(api_key, system_prompt, user_prompt):
    """
    调用 bltcy.ai 中转站 API，使用 gemini-3.1-flash-lite-preview 模型
    """
    url = "https://api.bltcy.ai/v1/chat/completions"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}', # 动态接收页面输入的 Key
        'User-Agent': 'DMXAPI/1.0.0',
        'Content-Type': 'application/json'
    }
    
    payload = json.dumps({
        "model": "gemini-3.1-flash-lite-preview",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    })
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status() # 检查 HTTP 错误
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ API 请求失败，请检查网络或 API Key 是否正确。\n错误详情: {e}"

# ==========================================
# 页面配置与初始化
# ==========================================
st.set_page_config(page_title="AI 深度阅读与拆解引擎", page_icon="📚", layout="wide")

if "generated_prompt" not in st.session_state:
    st.session_state.generated_prompt = ""

# ==========================================
# 侧边栏：全局设置 (API Key 输入区)
# ==========================================
with st.sidebar:
    st.header("⚙️ 全局设置")
    # 让用户在页面上输入 API Key
    api_key = st.text_input("请输入 API Key", type="password", help="你的 Key 仅在本次会话中有效，不会被保存。")
    
    st.markdown("---")
    st.markdown("### 🛠 模型配置")
    st.markdown("- **API 中转**: bltcy.ai")
    st.markdown("- **当前模型**: gemini-3.1-flash-lite-preview")

# ==========================================
# 主页面：双引擎交互区
# ==========================================
st.title("📚 AI 深度阅读与拆解引擎")
st.markdown("---")

# ------------------------------------------
# 步骤一：定义目标 (Engine A 生成动态指令)
# ------------------------------------------
st.header("Step 1: 定义文档元信息")
col1, col2 = st.columns(2)

with col1:
    doc_title = st.text_input("文档名称", placeholder="例如：How To Be A Games User Researcher")
    doc_type = st.selectbox("文档类型", ["专业方法论书籍", "市场/竞品研报", "长篇深度分析文章", "其他"])

with col2:
    user_intent = st.text_input("您的核心诉求", placeholder="例如：学习不同阶段的测试方法及流程")

doc_structure = st.text_area("原生结构 (目录/大纲)", height=150, 
                             placeholder="请粘贴书籍目录或报告大纲...\n例如：\n第一章：什么是游戏用研\n第二章：立项期的测试方法")

if st.button("✨ 生成专属阅读框架 (Generate Meta-Prompt)", type="primary"):
    if not api_key:
        st.warning("⚠️ 请先在左侧边栏输入 API Key！")
    elif not doc_title or not doc_structure:
        st.warning("⚠️ 请至少填写「文档名称」和「原生结构」！")
    else:
        with st.spinner("🧠 引擎 A 正在思考，为您定制阅读框架..."):
            # 构造 Meta-Prompt 的系统指令
            system_prompt = "你是一位顶级的 AI 知识架构师。你的任务是根据用户提供的书籍信息及其【原生结构】，动态生成一段用于“深度阅读与拆解”的专属 Prompt。请严格按照要求输出拆解框架，不需要任何废话。"
            
            # 构造用户输入的内容
            user_prompt = f"""
            - 文档名称：{doc_title}
            - 文档类型：{doc_type}
            - 核心诉求：{user_intent}
            - 原生结构：{doc_structure}
            
            请顺应原生结构逻辑，并紧密结合用户的核心诉求，生成拆解指令。格式如下：
            【系统指令】：你现在是一位资深阅读助手。请牢记用户的核心诉求：{user_intent}。
            【拆解路径与重点】：
            - 第一部分：[原书章节名] -> 重点提取：[结合诉求生成的提取目标]
            - 第二部分：[原书章节名] -> 重点提取：[结合诉求生成的提取目标]
            ...
            """
            
            # 调用封装好的 API 函数
            ai_response = call_ai_api(api_key, system_prompt, user_prompt)
            st.session_state.generated_prompt = ai_response
            st.success("✅ 专属阅读框架已生成！")

# ------------------------------------------
# 步骤二：框架微调 (Human-in-the-loop)
# ------------------------------------------
st.header("Step 2: 框架微调 (Human-in-the-loop)")
st.info("💡 下方是 AI 动态生成的指令。您可以直接在框内修改它。")

edited_prompt = st.text_area("专属拆解指令 (可编辑)", 
                             value=st.session_state.generated_prompt, 
                             height=250)

# ------------------------------------------
# 步骤三：执行阅读 (Engine B 拆解文档)
# ------------------------------------------
st.markdown("---")
st.header("Step 3: 上传文档并执行拆解")

uploaded_file = st.file_uploader("上传 PDF 样章 或 TXT 文件", type=["pdf", "txt"])

if st.button("🚀 开始深度拆解 (Execute Analysis)"):
    if not api_key:
        st.error("⚠️ 请先在左侧边栏输入 API Key！")
    elif not uploaded_file:
        st.error("⚠️ 请先上传要拆解的文档！")
    elif not edited_prompt:
        st.error("⚠️ 拆解指令不能为空，请先完成 Step 1。")
    else:
        with st.spinner("🤖 引擎 B 正在深度阅读与拆解中..."):
            
            # --- 这里模拟读取文件的文本 ---
            # 实际项目中这里需要用 PyMuPDF(fitz) 或 pdfplumber 来提取 PDF 文本
            # 目前我们先假设提取到了第一页的内容作为演示
            mock_extracted_text = "这里是程序从 PDF/TXT 中提取出的文本内容..." 
            
            # 调用 API 进行拆解 (Engine B)
            final_report = call_ai_api(
                api_key=api_key,
                system_prompt=edited_prompt, # 把刚刚生成的、用户确认过的 Prompt 当作系统指令
                user_prompt=f"请根据系统指令拆解以下内容：\n\n{mock_extracted_text}"
            )
            
            st.success("✅ 拆解完成！")
            st.markdown("### 📊 拆解结果展示")
            st.markdown(final_report)
