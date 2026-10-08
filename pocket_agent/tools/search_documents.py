"""把RAG检索能力包装成工具，让Agent能自己决定什么时候查资料"""
from .base import Tool
from pocket_agent.models import ToolResult
from pocket_agent.documents.retriever import Retriever

class search_documents(Tool):
    name="search_documents"
    description=(
        "查询内部资料库（产品说明书、售后政策、常见问题）。"
        "当用户询问产品参数、保修、退货、配送、价格等需要查证的问题时必须使用它。"
        "不要凭自己的记忆回答这类问题。"
    )
    parameters={
        "type":"object",
        "properties":{
            "query":{
                "type":"string",
                "description":"要检索的内容,例如退货政策，保修期限，发货时间等等"
            }
        },
        "required":["query"]
    }
    def __init__(self,retriever:Retriever):
        self.retriever=retriever
    def execute(self,query:str)->ToolResult:
        """返回检索结果"""
        result=self.retriever.retrieve(query)
        if not result:
            return ToolResult(content=f"没有找到与{query}相关的资料")
        blocks=[]
        for i,r in enumerate(result,1):
            blocks.append(f"第{i}条资料:\n{r['text']}\n来源:{r['source']}")
        return ToolResult(content="\n\n".join(blocks))
        
