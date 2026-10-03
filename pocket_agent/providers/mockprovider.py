from pocket_agent.providers.base import Provider
from pocket_agent.models import Message,LLMResponse
class MockProvider(Provider):
    @property
    def name(self)->str:
        return "MockProvider"
    def __init__(self,responses:list[LLMResponse],fallback:LLMResponse|None=None):
        self._responses=list(responses)
        self._fallback=fallback
        self.calls=[]
        self.tools_seen=[]
    def chat(self,messages:list[Message],tools:list[dict])->LLMResponse:
        self.calls.append(list(messages))
        self.tools_seen.append(list(tools))
        index=len(self.calls)-1
        if index<len(self._responses):
            return self._responses[index]
        if self._fallback:
            return self._fallback
        raise RuntimeError(
            f"MockProvider的剧本只有{len(self._responses)}条,却被调用了{len(self.calls)}次"
        )
        