"""这个文件写的是siliconflow的embedding接口，也就是硅基流动的embedding接口"""
from pocket_agent.documents.embedder import Embedder
from openai import OpenAI
from dotenv import load_dotenv
import os

class siliconflowembedder(Embedder):
    def __init__(self,model:str,api_key:str,base_url:str,dimension:int=1024):
        self.model=model
        self.dimension=dimension
        self.client=OpenAI(api_key=api_key,base_url=base_url)
    
    @classmethod
    def from_env(cls)->"siliconflowembedder":
        load_dotenv()
        Embedding_api_key=os.getenv("EMBEDDING_API_KEY")
        Embedding_base_url=os.getenv("EMBEDDING_BASE_URL")
        Embedding_model=os.getenv("EMBEDDING_MODEL")
        if not Embedding_api_key or not Embedding_base_url or not Embedding_model:
            raise RuntimeError("请在.env文件中设置正确的EMBEDDING_API_KEY,EMBEDDING_BASE_URL,EMBEDDING_MODEL")
        return cls(
            api_key=Embedding_api_key,
            base_url=Embedding_base_url,
            model=Embedding_model
        )

    @property
    def name(self)->str:
        return self.model

    @property
    def dimensions(self)->int:
        return self.dimension

    def embed(self,text:list[str])->list[list[float]]:
        if not text:
            return []
        response=self.client.embeddings.create(
            model=self.model,
            input=text
        )
        if len(response.data)!=len(text):
            raise RuntimeError("返回的向量总数与传入的文本长切块长度不同")
        embed_list=[]
        for i in response.data:
            embed_list.append(i.embedding)
        return embed_list
