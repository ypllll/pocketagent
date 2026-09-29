from pocket_agent.providers.base import Provider
from pocket_agent.models import Message,Runresult
from pocket_agent.tools.Tool_registry import ToolRegistry
class AgentRuntime:
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
            try:
                response=self.provider.chat(messages,self.tools.definitions())
            except Exception as e:
                return Runresult(
                    answer="模型调用失败,失败原因是：{e}",
                    stop_reason="error",
                    message=messages
                )
            messages.append(Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls
            ))
            if not response.should_execute_tools:
                return Runresult(
                    answer=response.content,
                    stop_reason="completed",
                    message=messages
                )
            for tool_call in response.tool_calls:
                result=self.tools.execute(tool_call.name,tool_call.arguments)
                messages.append(Message(
                    role="tool",
                    content=result.content,
                    tool_call_id=tool_call.id
                ))
        return Runresult(
            answer="步数用尽，没能在规定循环内完成任务",
            stop_reason="max_iterations",
            message=messages
        )
