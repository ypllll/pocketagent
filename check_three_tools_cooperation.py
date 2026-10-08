"""端到端跑一次：三个工具协同的客服场景"""

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

PDF = r"D:\pocketagent\samples\iPhoneDuo_产品说明书.pdf"
CHROMA = r"D:\pocketagent\data\chroma"
DB = r"D:\pocketagent\data\pocket.db"

# 1) 知识库（已入库就跳过）
store = Vector_store(CHROMA, "documents", siliconflowembedder.from_env())
if store.count() == 0:
    print(f"首次入库：{ingest_document(PDF, store)} 条")
else:
    print(f"库里已有 {store.count()} 条，跳过")

# 2) 两阶段检索
retriever = Retriever(store, siliconflowreranker.from_env(), top_k=5, top_n=3)

# 3) 注册三个工具
tools = ToolRegistry()
tools.register(search_documents(retriever))
tools.register(query_order())
tools.register(create_ticket(DB))
print("已注册工具:", tools.tools_name())

# 4) 跑
runtime = AgentRuntime(provider=OpenaiProvider.from_env(), tools=tools, max_step=10)
result = runtime.run("订单 ORD-5678 我要投诉！凭什么不能退？")

# 5) 打印
print("\n最终答案：", result.answer)
print("\n停止原因：", result.stop_reason)

print("\n调用轨迹：")
for t in result.trace:
    line = (f"step:{t.step:<2} kind:{t.kind:<8} name:{t.name:<18} "
            f"elapsed_ms:{t.elapsed_ms:>5}ms")
    if t.is_error:
        line += "   [ERROR]"
    if t.detail:
        line += f"   detail:{t.detail[:80]}"
    print(line)

called = [t.name for t in result.trace if t.kind == "tool"]
print("\n工具调用顺序：", called)