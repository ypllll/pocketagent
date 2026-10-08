"""PocketAgent 客服助手 —— Streamlit 界面

运行方式（在 D:\\pocketagent 目录下）：
    & "C:\\Users\\siuuu\\miniconda3\\envs\\ai_env\\python.exe" -m streamlit run app.py
"""

import re
import tempfile
from pathlib import Path

import chromadb
import streamlit as st

from pocket_agent.documents.SiliconFlowEmbedder import siliconflowembedder
from pocket_agent.documents.ingest_document import ingest_document
from pocket_agent.documents.reranker import siliconflowreranker
from pocket_agent.documents.retriever import Retriever
from pocket_agent.documents.vector_store import Vector_store
from pocket_agent.providers.openai_provider import OpenaiProvider
from pocket_agent.runtime.loop import AgentRuntime
from pocket_agent.tools.create_ticket import create_ticket
from pocket_agent.tools.query_order import query_order
from pocket_agent.tools.search_documents import search_documents
from pocket_agent.tools.Tool_registry import ToolRegistry

BASE_DIR = Path(r"D:\pocketagent")
CHROMA_DIR = str(BASE_DIR / "data" / "chroma")
DB_PATH = str(BASE_DIR / "data" / "pocket.db")

st.set_page_config(page_title="PocketAgent 客服助手", page_icon="🤖", layout="wide")


# ----------------------------------------------------------------------------
# 组装 Agent（只做一次）
#
# Streamlit 的机制：用户每敲一次回车，整个脚本会从头重跑一遍。
# 如果把 Vector_store / Retriever / Provider 建在模块顶层，
# 每次交互都会重新连数据库、重新读 .env —— 又慢又浪费。
# @st.cache_resource 让这些"重对象"只构造一次，之后一直复用。
# ----------------------------------------------------------------------------
@st.cache_resource(show_spinner="正在启动 Agent…")
def build_agent():
    store = Vector_store(CHROMA_DIR, "documents", siliconflowembedder.from_env())
    retriever = Retriever(store, siliconflowreranker.from_env(), top_k=5, top_n=3)

    tools = ToolRegistry()
    tools.register(search_documents(retriever))
    tools.register(query_order())
    tools.register(create_ticket(DB_PATH))

    runtime = AgentRuntime(provider=OpenaiProvider.from_env(), tools=tools, max_step=10)
    return runtime, store


SOURCE_RE = re.compile(r"^\[资料(\d+)\]\s*来源：(.+?)\s*第(\d+)块$")


def extract_sources(tool_output: str) -> list[dict]:
    """从 search_documents 的返回里把 [资料N] 来源：xx 第M块 摘出来"""
    found = []
    for line in tool_output.splitlines():
        m = SOURCE_RE.match(line.strip())
        if m:
            found.append({"no": m.group(1), "source": m.group(2), "block": m.group(3)})
    return found


def pair_tool_outputs(messages) -> list[dict]:
    """把 role='tool' 的消息和它的工具名配上对

    tool 消息本身只有 tool_call_id，工具名在它前面那条 assistant 消息的 tool_calls 里。
    """
    id2name = {}
    for msg in messages:
        for call in msg.tool_calls or []:
            id2name[call.id] = call.name

    pairs = []
    for msg in messages:
        if msg.role == "tool":
            pairs.append({
                "name": id2name.get(msg.tool_call_id, "未知工具"),
                "content": msg.content or "",
            })
    return pairs


def render_turn(turn: dict) -> None:
    """渲染一轮助手回复：答案 + 来源 + 轨迹"""
    st.markdown(turn["content"])

    # ---- 来源 ----
    sources = []
    for out in turn.get("tool_outputs", []):
        if out["name"] == "search_documents":
            sources.extend(extract_sources(out["content"]))
    if sources:
        with st.expander(f"📚 资料来源（{len(sources)} 条）"):
            for s in sources:
                st.markdown(f"- **[资料{s['no']}]** {s['source']} · 第 {s['block']} 块")

    # ---- 执行轨迹 ----
    trace = turn.get("trace", [])
    if trace:
        tool_count = sum(1 for t in trace if t.kind == "tool")
        total_ms = sum(t.elapsed_ms for t in trace)
        with st.expander(f"🧭 执行轨迹（{tool_count} 次工具调用 · {total_ms} ms）"):
            st.table([
                {
                    "步骤": t.step,
                    "类型": "模型" if t.kind == "model" else "工具",
                    "名称": t.name,
                    "耗时(ms)": t.elapsed_ms,
                    "状态": "❌ 出错" if t.is_error else "✅ 正常",
                    "详情": (t.detail or "")[:70],
                }
                for t in trace
            ])

    # ---- 完整工具返回（含工单号等）----
    for out in turn.get("tool_outputs", []):
        if out["name"] != "search_documents":
            with st.expander(f"🔧 {out['name']} 的完整返回"):
                st.code(out["content"], language=None)


# ----------------------------------------------------------------------------
# 侧边栏：知识库状态 + 上传 + 清空
# ----------------------------------------------------------------------------
runtime, store = build_agent()

with st.sidebar:
    st.header("📁 知识库")
    st.metric("已入库片段", store.count())

    uploaded = st.file_uploader("上传资料（PDF / TXT / MD）", type=["pdf", "txt", "md"])
    if uploaded is not None and st.button("导入这份资料", type="primary"):
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_file = tmp_dir / uploaded.name
        tmp_file.write_bytes(uploaded.getbuffer())
        with st.spinner("正在解析、切块、向量化…"):
            n = ingest_document(str(tmp_file), store)
        st.success(f"已导入 {n} 块")
        st.rerun()

    st.divider()
    st.caption("演示用订单号")
    st.code("ORD-1234  签收 5 天，可退\n"
            "ORD-5678  签收 18 天，超期\n"
            "ORD-9012  定制刻字，不可退\n"
            "ORD-3456  运输中，未签收\n"
            "ORD-9999  不存在", language=None)

    st.divider()
    if st.button("⚠️ 清空知识库", help="删除所有已入库的文档片段，不可撤销"):
        try:
            chromadb.PersistentClient(path=CHROMA_DIR).delete_collection("documents")
        except Exception:
            pass          # 库本来就是空的，忽略
        st.cache_resource.clear()
        st.session_state.pop("turns", None)
        st.success("已清空，正在重启…")
        st.rerun()


# ----------------------------------------------------------------------------
# 主区域：聊天
# ----------------------------------------------------------------------------
st.title("🤖 PocketAgent 客服助手")
st.caption("我会先查资料、再回答。涉及订单退换时会自己查询订单并判断。")

if "turns" not in st.session_state:
    st.session_state.turns = []

for turn in st.session_state.turns:
    with st.chat_message("user"):
        st.markdown(turn["question"])
    with st.chat_message("assistant"):
        render_turn(turn)

question = st.chat_input("请输入你的问题，例如：订单 ORD-1234 能退货吗？")

if question:
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("思考中…"):
            result = runtime.run(question)

        turn = {
            "question": question,
            "content": result.answer or "（模型没有返回内容）",
            "trace": result.trace,
            "tool_outputs": pair_tool_outputs(result.message),
            "stop_reason": result.stop_reason,
        }
        render_turn(turn)

        if result.stop_reason != "completed":
            st.warning(f"本轮没有正常结束，停止原因：{result.stop_reason}")

    st.session_state.turns.append(turn)
