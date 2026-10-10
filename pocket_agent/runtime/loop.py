from pocket_agent.providers.base import Provider
from pocket_agent.models import Message,Runresult
from pocket_agent.tools.Tool_registry import ToolRegistry
import time
from pocket_agent.observability.trace import TraceRecorder
import json
SYSTEM_PROMPT = (
    "你是 iPhoneDuo 的官方在线客服。\n\n"
    "工作方式：\n"
    "1. 涉及产品参数、价格、保修、退货、换货、发货的问题，必须先调用 search_documents 查证，不许凭记忆回答。\n"
    "2. 判断某个订单能否退换时，要同时检查两件事："
    "① 签收时间是否在政策规定的期限内；② 商品是否属于政策里的除外情形（例如定制刻字机型、已拆封的贴膜配件）。"
    "两项都满足才能答复『可以』。\n"
    "3. 需要知道订单信息时，调用 query_order 查询；如果订单号查不到，请用户确认，不要猜测。\n"
    "4. 如果资料里没有相关内容，如实说『我这边没有查到相关信息』。\n"
    "5. 涉及退款金额、赔偿承诺，必须调用 create_ticket 创建工单，并说明由人工跟进\n"
    "6. 当用户表达不满、投诉，或明确要求人工处理时，必须调用 create_ticket 创建工单，不要只是口头问'需要转人工吗'\n"
    "7. 回答时先说明判断依据（用户的订单是什么情况、引用了哪条政策），再告知已经/将要采取的行动（例如已创建工单）。不要只说'已创建工单'而不解释原因。\n\n"
    "回答要求：\n"
    "- 始终使用简体中文回答，不要夹杂英文。\n"
    "- 简洁准确，提到政策时说明来自哪份资料。"
    "- 不要罗列与用户问题无关的条款。"
)
class AgentRuntime:
    def __init__(self,provider:Provider,tools:ToolRegistry,max_step=8):
        self.provider=provider
        self.tools=tools
        self.max_step=max_step

    def run(self,user_input)->Runresult:
        traces=TraceRecorder()
        messages=[
            Message(role="system",content=SYSTEM_PROMPT),
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
                query=json.dumps(tool_call.arguments,ensure_ascii=False)
                traces.record(
                    step=step,
                    kind="tool",
                    name=tool_call.name,
                    elapsed_ms=int((time.perf_counter()-t1)*1000),
                    is_error=result.is_error,
                    detail=f"{query}->{result.content[:120]}"
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
