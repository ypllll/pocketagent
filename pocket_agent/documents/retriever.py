"""本文件写的是结合reranker和vector_store两阶段检索，得出最后与query最相关的chunk"""

from pocket_agent.documents.vector_store import Vector_store
from pocket_agent.documents.reranker import siliconflowreranker

class Retriever:
    def __init__(self,store:Vector_store,reranker:siliconflowreranker,top_k=10,top_n:int=3):
        self.store=store
        self.reranker=reranker
        self.top_k=top_k
        self.top_n=top_n

    def retrieve(self,query:str)->list[dict]:
        candidates=self.store.search(query,top_k=self.top_k)
        if not candidates:
            return []
        text_candidates=[c["text"] for c in candidates]
        sort_results=self.reranker.rerank(query,text_candidates,top_n=self.top_n)
        result=[]
        for i in sort_results:
            chunk=candidates[i["index"]]
            result.append({
                "text":chunk["text"],
                "source":chunk["source"],
                "index":chunk["index"],
                "distance":chunk["distance"],
                "rerank_score":i["score"]
            })
        return result
