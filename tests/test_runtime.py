from pocket_agent.runtime.loop import AgentRuntime
from pocket_agent.providers.mockprovider import MockProvider
from pocket_agent.tools.Tool_registry import ToolRegistry
from pocket_agent.tools.get_weather import get_weather
from pocket_agent.models import LLMResponse,ToolCall
#险些一个帮手函数，目的是把工具注册到注册表里面，同时构建好一个runtime
def help(provider):
    regis=ToolRegistry()
    regis.register(get_weather())
    return AgentRuntime(provider,regis)
#先测试不用调用工具的版本
def test_不用调用工具():
    mock=MockProvider([LLMResponse(content="你好，我叫pocket agent")])
    runtime=help(mock)
    result=runtime.run("你好")

    assert result.stop_reason=="completed"
    assert result.answer=="你好，我叫pocket agent"
    assert len(result.message)==3
    assert len(mock.calls)

def make_script():
    return [
        LLMResponse(
            tool_calls=[
                ToolCall(
                    id="c1",
                    name="get_weather",
                    arguments={"city":"北京"}
                )
            ],
            finish_reason="tool_calls"
        ),
        LLMResponse(content="北京今日天气晴，25°C")
    ]
def test_用一次工具再回答():
    mock=MockProvider(make_script())
    runtime=help(mock)
    result=runtime.run("北京今天天气怎么样？")

    assert result.stop_reason=="completed"
    assert len(result.message)==5
    assert result.message[3].role=="tool"
    assert "北京" in result.message[3].content
    assert len(mock.calls)==2

def test_工具说明书传给了模型():
    mock=MockProvider(make_script())
    runtime=help(mock)
    result=runtime.run("北京今天天气怎么样？")

    assert mock.tools_seen[0] is not None
    assert mock.tools_seen[0][0]["function"]["name"]=="get_weather"

def test_步数用尽():
    mock=MockProvider(
        [],
        LLMResponse(
            tool_calls=[ToolCall(
                id="c1",
                name="get_weather",
                arguments={"city":"北京"}
            )],
            finish_reason="tool_calls"
        )
    )
    regis=ToolRegistry()
    regis.register(get_weather())
    runtime=AgentRuntime(mock,regis,max_step=3)
    result=runtime.run("一直查天气")

    assert result.stop_reason=="max_iterations"
    assert len(mock.calls)==3
    assert result.answer is not None

def test_工具失败时循环继续():
    mock=MockProvider([
        LLMResponse(
            tool_calls=[ToolCall(
                id="c1",
                name="get_weather",
                arguments={"city":"火星"}
            )]
        ),
        LLMResponse(content="查不到火星的天气")
    ])
    runtime=help(mock)
    result=runtime.run("我想查询火星的天气")

    assert result.stop_reason=="completed"
    assert "火星" in result.message[3].content

def test_模型调用失败():
    mock=MockProvider([])
    runtime=help(mock)
    result=runtime.run("测试失败案例")

    assert result.stop_reason=="error"
    assert "失败" in result.answer



