from .base import Tool
from pocket_agent.models import ToolResult
class search_note(Tool):
    name="search_note"
    description="在本地笔记里检索内容"
    parameters={
        "type":"object",
        "properties":{
            "query":{"type":"string","description":"检索关键词"},
            "top_s":{"type":"integer","description":"最多返回几条"}
        },
        "required":["query"]
        
    }
    _NOTES = [
    "Agent Loop 的停止条件包括最终答案、最大步数、超时与出错。",
    "Tool Calling 要求 assistant 先声明 tool_calls，再为每个 tool_call_id 提供 tool 消息。",
    "上下文压缩不是删除原文，而是用摘要替换重放前缀，并移动重放起点。",
    "RAG 的第一步是把文档切成 chunk，并保留页码等元数据以便溯源。",
    ]
    def execute(self, query:str,top_s:int=2):
        lines=[note for note in self._NOTES if query in note]
        if lines is None:
            return ToolResult(content="没有找到与检索词符合的内容")
        return ToolResult(content="\n".join(lines[:top_s]))
        
        