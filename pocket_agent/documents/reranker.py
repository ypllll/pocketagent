"""现在是RAG流程的第五步，这一步是把vector_store召回的候选重新打分排序，最后选出top_n个与用户提问最相关的chunk"""
import requests
import os
from dotenv import load_dotenv    
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

class siliconflowreranker:
    def __init__(self,model:str,api_key:str,base_url:str):
        self.model=model
        self.api_key=api_key
        self.base_url=base_url

    @classmethod
    def from_env(cls)->"siliconflowreranker":
        load_dotenv()
        embedding_api_key=os.getenv("EMBEDDING_API_KEY")
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL")
        if not embedding_api_key or not embedding_base_url:
            raise RuntimeError(f".env文件中缺少了{embedding_base_url}或是{embedding_api_key}，请检查后再试")
        return cls(
            model=RERANK_MODEL,
            api_key=embedding_api_key,
            base_url=embedding_base_url
        )

    def rerank(self,query:str,documents:list[str],top_n=3)->list[dict]:
        if not documents:
            return []
        url=f"{self.base_url}/rerank"
        headers={
            "Content-Type":"application/json",
            "Authorization":f"Bearer {self.api_key}"
        }
        body={
            "model":self.model,
            "query":query,
            "documents":documents,
            "top_n":top_n
        }
        response=requests.post(url,json=body,headers=headers,timeout=30)
        if response.status_code!=200:
            raise RuntimeError(f"请求rerank接口失败,返回{response.status_code}:{response.text}")
        data=response.json()
        return[
            {"index":i["index"],"score":i["relevance_score"]}
            for i in data["results"]
        ]
    


        