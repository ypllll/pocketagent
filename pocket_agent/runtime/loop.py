from pocket_agent.providers.base import Provider
from pocket_agent.models import Message,Runresult
from pocket_agent.tools.Tool_registry import ToolRegistry
class Runtime:
    def __init__(self,provider:Provider,tools:ToolRegistry,max_step=8):
        self.provider=provider
        self.tools=tools
        self.max_step=max_step

    def run(self,user_input)->Runresult:
        messages=[
            Message(role="system",content="你是一个研究助手，需要时要调用外部工具"),
            Message(role="user",content=user_input)
        ]
        for _ in range(self.max_step):
            response=self.provider.chat(messages,self.tools.definitions())
            messages.append(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls
            )
            if not response.should_execute_tools:
                return Runresult(
                    answer=response.content,
                    stop_reason="conpleted",
                    message=messages
                )
            for tool_call in response.tool_calls:
                result=self.tools.execute(tool_call.name,tool_call.arguments)
                messages.append(
                    role="tool",
                    content=result.content,
                    tool_call_id=tool_call.id
                )
        return Runresult(
            content="步数用尽，没能在规定循环内完成任务",
            stop_reason="max_iterations",
            message=messages
        )
