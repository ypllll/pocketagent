from pocket_agent.providers.base import Provider
from pocket_agent.models import Message,Runresult
from pocket_agent.tools.Tool_registry import ToolRegistry
import time
from pocket_agent.observability.trace import TraceRecorder
class AgentRuntime:
    def __init__(self,provider:Provider,tools:ToolRegistry,max_step=8):
        self.provider=provider
        self.tools=tools
        self.max_step=max_step

    def run(self,user_input)->Runresult:
        traces=TraceRecorder()
        messages=[
            Message(role="system",content="你是一个研究助手，需要时要调用外部工具"),
            Message(role="user",content=user_input)
        ]
        for step in range(1,self.max_step+1):
            try:
                t0=time.perf_counter()
                response=self.provider.chat(messages,self.tools.definitions())
            except Exception as e:
                return Runresult(
                    answer=f"模型调用失败,失败原因是：{e}",
                    stop_reason="error",
                    message=messages,
                    trace=traces.steps
                )
            traces.record(
                    step=step,
                    kind="model",
                    name=self.provider.name,
                    elapsed_ms=int((time.perf_counter()-t0)*1000),
                    detail=f"finish_reason:{response.finish_reason}"
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
                    message=messages,
                    trace=traces.steps
                )
            for tool_call in response.tool_calls:
                t1=time.perf_counter()
                result=self.tools.execute(tool_call.name,tool_call.arguments)
                traces.record(
                    step=step,
                    kind="tool",
                    name=tool_call.name,
                    elapsed_ms=int((time.perf_counter()-t1)*1000),
                    is_error=result.is_error,
                    detail=result.content[:50]
                )
                messages.append(Message(
                    role="tool",
                    content=result.content,
                    tool_call_id=tool_call.id
                ))
        return Runresult(
            answer="步数用尽，没能在规定循环内完成任务",
            stop_reason="max_iterations",
            message=messages,
            trace=traces.steps
        )
