from abc import ABC,abstractmethod
from pocket_agent.models import Message,LLMResponse
class Provider(ABC):
    """用于trace显示，子类可重写"""
    @property
    def name(self)->str:
        return self.__class__.__name__
    @abstractmethod
    def chat(self,messages:list[Message],tools:list[dict])->LLMResponse:
        ...