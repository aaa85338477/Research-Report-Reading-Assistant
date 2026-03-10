import streamlit as st
import requests
import json
import fitz  # PyMuPDF，用于解析 PDF 目录和提取文本

# ==========================================
# 核心通信模块：调用大模型 API
# ==========================================
def call_ai_api(api_key, system_prompt, user_prompt):
    """
    调用 bltcy.ai 中转站 API，使用 gemini-3.1-flash-lite-preview 模型
    """
    url = "https://api.bltcy.ai/v1/chat/completions"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}', 
        'User-Agent': 'DMXAPI/1.0.0',
        'Content-Type': 'application/json'
    }
    
    payload = json.dumps({
        "model": "gemini-3.1-flash-lite-preview",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    })
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status() 
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ API 请求失败，请检查网络或 API Key 是否正确。\n错误详情: {e}"

# ==========================================
# 核心处理模块：PDF 智能解析
# ==========================================
def extract_pdf_structure(uploaded_file):
    """提取 PDF 原生目录树"""
    try:
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        toc = doc.get_toc() 
        
        if toc:
            structure_text = ""
            for item in toc:
                level, title, page = item
                indent = "  " * (level - 1)
                structure_text += f"{indent}- {title} (第{page}页)\n"
            return structure_text
        else:
            return "⚠️ 未检测到 PDF 原生书签。请在此手动输入，或简述文档大纲..."
    except Exception as e:
        return f"解析 PDF 目录失败: {e}"

def extract_pdf_text(uploaded_file, max_pages=5):
    """提取 PDF 正文内容（默认提取前 max_pages 页）"""
    try:
        uploaded_file.seek(0) 
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for i in range(min(max_pages, len(doc))):
            text += doc[i].get_text()
        return text
    except Exception as e:
        return f"提取正文失败: {e}"

# ==========================================
# UI 页面配置与状态初始化
# ==========================================
st.set_page_config(page_title="AI 深度阅读与拆解引擎", page_icon="📚", layout="wide")

# 初始化所有的 Session State，确保页面刷新时数据不丢失
if "auto_structure" not in st.session_state:
    st.session_state.auto_structure = ""
if "generated_prompt" not in st.session_state:
    st.session_state.generated_prompt = ""
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "final_report" not in st.session_state:
    st.session_state.final_report = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==========================================
# 侧边栏：全局设置与安全认证
# ==========================================
with st.sidebar:
    st.header("⚙️ 全局设置")
    api_key = st.text_input("🔑 请输入 API Key", type="password", help="仅在当前会话有效，安全且不会被记录。")
    
    st.markdown("---")
    st.markdown("### 🛠 引擎状态")
    st.markdown("- **解析引擎**: PyMuPDF")
    st.markdown("- **推理模型**: gemini-3.1-flash-lite-preview")
    st.markdown("- **交互模式**: 双引擎 + 深度追问")

# ==========================================
# 主页面：业务流转区
# ==========================================
st.title("📚 AI 深度阅读与拆解引擎")
st.markdown("> **设计理念**：针对复杂研报与专业书籍，摒弃粗暴的“全文总结”，采用**结构感知 (Structure-Aware)** 机制，顺应文档原生骨架进行业务级维度的深度拆解，并提供基于上下文的深度问答。")
st.markdown("---")

# ------------------------------------------
# Step 1: 文档上传与结构解析
# ------------------------------------------
st.header("Step 1: 上传文档与智能解析")

uploaded_file = st.file_uploader("📂 请上传需要拆解的 PDF 研报或书籍", type=["pdf"])

if uploaded_file:
    if st.button("🔍 自动提取文档骨架", type="secondary"):
        with st.spinner("正在解析 PDF 原生目录..."):
            st.session_state.auto_structure = extract_pdf_structure(uploaded_file)
            st.success("✅ 骨架提取完成！请在下方核对并补充信息。")

col1, col2 = st.columns(2)
with col1:
    doc_title = st.text_input("文档名称", placeholder="例如：海外休闲游戏买量白皮书")
    doc_type = st.selectbox("文档类型", ["专业方法论书籍", "市场/竞品研报", "长篇深度分析文章", "其他"])

with col2:
    user_intent = st.text_input("🎯 您的核心诉求", placeholder="例如：重点关注 LTV 模型构建和买量成本测算")

doc_structure = st.text_area("原生结构 (AI 已自动提取，支持手动微调)", 
                             value=st.session_state.auto_structure,
                             height=180)

# ------------------------------------------
# Step 2: 引擎 A - 生成专属阅读框架
# ------------------------------------------
st.markdown("---")
st.header("Step 2: 引擎 A - 生成专属拆解指令")

if st.button("✨ 基于骨架与诉求生成专属指令 (Generate Meta-Prompt)", type="primary"):
    if not api_key:
        st.warning("⚠️ 请先在左侧边栏输入 API Key！")
    elif not doc_title or not doc_structure:
        st.warning("⚠️ 请确保「文档名称」和「原生结构」已填写！")
    else:
        with st.spinner("🧠 引擎 A 正在动态构筑阅读框架..."):
            system_prompt = "你是一位顶级的 AI 知识架构师。你的任务是根据用户提供的文档信息及其【原生结构】，动态生成一段用于“深度阅读与拆解”的专属 Prompt。请严格按照要求输出拆解框架，不需要任何废话。"
            
            user_prompt = f"""
            - 文档名称：{doc_title}
            - 文档类型：{doc_type}
            - 核心诉求：{user_intent}
            - 原生结构：\n{doc_structure}
            
            请顺应原生结构逻辑，紧密结合用户的核心诉求，生成拆解指令。格式严格如下：
            【系统指令】：你现在是一位资深阅读助手。请牢记用户的核心诉求：{user_intent}。
            【拆解路径与重点】：
            - 第一部分：[原书章节名] -> 重点提取：[结合诉求生成的提取目标]
            - 第二部分：[原书章节名] -> 重点提取：[结合诉求生成的提取目标]
            ...
            """
            
            st.session_state.generated_prompt = call_ai_api(api_key, system_prompt, user_prompt)
            st.success("✅ 专属阅读指令已生成！这是 AI 在阅读前形成的“心智模型”。")

st.info("💡 引入 **Human-in-the-loop** 机制，您可以直接在框内修改生成的指令，进行最终干预。")
edited_prompt = st.text_area("专属拆解指令 (可编辑)", 
                             value=st.session_state.generated_prompt, 
                             height=200)

# ------------------------------------------
# Step 3: 引擎 B - 执行深度拆解
# ------------------------------------------
st.markdown("---")
st.header("Step 3: 引擎 B - 执行深度拆解")

if st.button("🚀 开始深度拆解 (Execute Analysis)"):
    if not api_key:
        st.error("⚠️ 请先在左侧边栏输入 API Key！")
    elif not uploaded_file:
        st.error("⚠️ 找不到 PDF 文件，请重新上传！")
    elif not edited_prompt:
        st.error("⚠️ 拆解指令为空，请先完成 Step 2！")
    else:
        with st.spinner("🤖 引擎 B 正在通读正文并执行结构化拆解 (演示模式仅提取前5页)..."):
            
            # 1. 真实提取 PDF 正文文本并存入 session_state
            st.session_state.extracted_text = extract_pdf_text(uploaded_file, max_pages=5)
            
            if not st.session_state.extracted_text.strip():
                st.error("⚠️ 无法从 PDF 中提取到有效文本，可能是扫描版或已加密。")
            else:
                # 2. 调用引擎 B 进行最终总结，要求结尾不反问
                execute_prompt = edited_prompt + "\n\n【重要纪律要求】：报告结尾必须干脆利落，严禁在最后提出反问、寒暄或询问用户是否需要进一步解答。"
                
                final_report = call_ai_api(
                    api_key=api_key,
                    system_prompt=execute_prompt,
                    user_prompt=f"请严格根据系统指令，拆解以下文档内容：\n\n{st.session_state.extracted_text}"
                )
                
                # 3. 将生成的报告存入 session_state
                st.session_state.final_report = final_report
                
                # 4. 初始化一句欢迎提问的开场白
                st.session_state.chat_history = [{"role": "assistant", "content": "您好！报告已拆解完毕。关于上述内容，您有任何想要深入探讨的细节吗？"}]
                st.success("✅ 拆解完成！")

# 如果已经生成了报告，则展示报告内容
if st.session_state.final_report:
    st.markdown("### 📊 最终结构化研报")
    st.markdown(st.session_state.final_report)

# ------------------------------------------
# Step 4: 针对研报的深度追问 (Interactive Q&A)
# ------------------------------------------
# 只有当提取了文本并生成了报告后，才渲染聊天模块
if st.session_state.extracted_text and st.session_state.final_report:
    st.markdown("---")
    st.header("Step 4: 深度追问 (Interactive Q&A)")
    
    # 渲染历史对话气泡
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 聊天输入框 (st.chat_input 默认固定在页面底部)
    user_question = st.chat_input("针对刚才的研报，输入你想深入了解的问题...")

    if user_question:
        if not api_key:
            st.error("⚠️ 请在左侧边栏输入 API Key 以继续对话！")
        else:
            # 1. 显示用户的提问并存入历史
            with st.chat_message("user"):
                st.markdown(user_question)
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            
            # 2. 显示 AI 的思考状态与回答
            with st.chat_message("assistant"):
                with st.spinner("正在检索文档上下文并思考..."):
                    # 构建包含文档上下文的 Prompt
                    qa_system_prompt = "你是一位专业的业务研究助理。请严格基于用户提供的【文档上下文】回答问题。如果文档中没有相关信息，请明确告知，切勿根据自己的知识库盲目编造。"
                    
                    qa_user_prompt = f"""
                    【文档上下文】：
                    {st.session_state.extracted_text}
                    
                    【用户追问】：
                    {user_question}
                    """
                    
                    answer = call_ai_api(api_key, system_prompt=qa_system_prompt, user_prompt=qa_user_prompt)
                    st.markdown(answer)
                    
            # 3. 将 AI 的回答存入历史
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
