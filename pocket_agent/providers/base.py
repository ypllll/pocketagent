from abc import ABC,abstractmethod
from pocket_agent.models import Message,LLMResponse
class Provider(ABC):
    @abstractmethod
    def chat(self,messages:list[Message],tools:list[dict])->LLMResponse:
        ...