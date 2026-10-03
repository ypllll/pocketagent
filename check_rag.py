"""检查 RAG 流水线的前两步：文档解析 + 切块。

用法（在 D:\pocketagent 目录下）：
    python check_rag.py
"""

from pocket_agent.documents.chunker import chunk_text
from pocket_agent.documents.loaders import load_document

PDF = "samples/iPhoneDuo_产品说明书.pdf"
SIZE = 400
OVERLAP = 50

print("=" * 55)
print("① 解析文档")
text = load_document(PDF)
print(f"   文件：{PDF}")
print(f"   提取到 {len(text)} 个字符")
print(f"   开头：{text[:40]!r}")

print()
print("② 切块")
chunks = chunk_text(text, source=PDF, chunk_size=SIZE, chunk_overlap=OVERLAP)
print(f"   参数：chunk_size={SIZE}, chunk_overlap={OVERLAP}")
print(f"   块数：{len(chunks)}")
for c in chunks:
    print(f"   #{c['index']}  长度={len(c['text']):>4}  开头={c['text'][:22]!r}")

print()
print("③ 重叠验证（相邻块应有 50 字重合）")
if len(chunks) >= 2:
    same = chunks[0]["text"][-OVERLAP:] == chunks[1]["text"][:OVERLAP]
    print(f"   第0块结尾50字 == 第1块开头50字 : {same}")
else:
    same = False
    print("   块数不足 2，无法验证重叠")

print()
print("=" * 55)
if chunks and same:
    print("RAG 前两步完成 ✅")
else:
    print("有问题，检查上面的输出 ❌")
