"""这个是RAG工作流程的第三步，就是把长文本切成的chunkembedding成向量，现在先写一个抽象接口"""
from abc import ABC, abstractmethod
class Embedder(ABC):
    @property
    @abstractmethod
    def name(self)->str:
        """返回embedding模型的名称"""

    @property
    @abstractmethod
    def dimensions(self)->int:
        """返回embedding向量的维度"""

    def embed(self,text:str)->list[list[float]]:
        """把文本embedding成向量"""