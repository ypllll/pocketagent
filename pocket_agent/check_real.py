from pocket_agent.providers.openai_provider import OpenaiProvider
from pocket_agent.runtime.loop import AgentRuntime
from pocket_agent.tools.Tool_registry import ToolRegistry
from pocket_agent.tools.get_weather import get_weather
from pocket_agent.tools.search_note import search_note

provider=OpenaiProvider.from_env()
tools=ToolRegistry()
tools.register(get_weather())
tools.register(search_note())
runtime=AgentRuntime(provider,tools,max_step=8)
result=runtime.run("请帮我查一下广州的天气")

print("最终答案：",result.answer)
print("停止原因：",result.stop_reason)
print("消息记录：")
for message in result.message:
    print(f"{message.role:<9}: {str(message.content)[:50]}")
print("调用轨迹：")
for trace in result.trace:
    print(
        f"step:{trace.step:<2} kind:{trace.kind:<8} name:{trace.name:<15} elapsed_ms:{trace.elapsed_ms:>5}ms"
        +("   [ERROR]" if trace.is_error else "")
        +(f"   detail:{trace.detail}" if trace.detail else "")
    )
