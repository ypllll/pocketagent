import pytest
from pocket_agent.models import ToolCall,LLMResponse,Message
from pocket_agent.providers.mockprovider import MockProvider
def make_script():
    return[
        LLMResponse(
            tool_calls=[ToolCall(id="c1",name="get_weather",arguments={"city":"北京"})],
            finish_reason="tool_calls"
        ),
        LLMResponse(content="北京天气晴，28摄氏度")
    ]

def make_history():
    return [
        Message(role="system",content="你是天气助手"),
        Message(role="user",content="北京天气怎么样")
    ]

def test_第一轮测试():
    mock=MockProvider(make_script())
    response=mock.chat(make_history(),[])
    assert response.finish_reason=="tool_calls"
    assert response.tool_calls[0].name=="get_weather"

def test_第二轮测试():
    mock=MockProvider(make_script())
    history=make_history()+[
        Message(
            role="assistant",
            tool_calls=[ToolCall(id="c1",name="get_weather",arguments={"city":"北京"})]
        ),
        Message(role="tool",content="北京天气晴，28摄氏度")
    ]
    mock.chat(make_history(),[])
    response=mock.chat(history,[])
    assert response.content=="北京天气晴，28摄氏度"

def test_第三轮测试():
    mock=MockProvider(make_script())
    history=make_history()+[
            Message(
                role="assistant",
                tool_calls=[ToolCall(id="c1",name="get_weather",arguments={"city":"北京"})]
            ),
            Message(role="tool",content="北京天气晴，28摄氏度")
        ]
    mock.chat(make_history(),[])
    mock.chat(history,[])
    with pytest.raises(RuntimeError):
        mock.chat(history,[])

def test_测试剧本走完后的兜底():
    mock=MockProvider(
        make_script(),
        fallback=LLMResponse(
            content="剧本已经走完了，这是兜底"
        )
    )
    history=make_history()+[
                Message(
                    role="assistant",
                    tool_calls=[ToolCall(id="c1",name="get_weather",arguments={"city":"北京"})]
                ),
                Message(role="tool",content="北京天气晴，28摄氏度")
            ]
    mock.chat(make_history(),[])
    mock.chat(history,[])
    response=mock.chat(history,[])
    assert response.content=="剧本已经走完了，这是兜底"

def test_被调用的次数():
    mock=MockProvider(make_script())
    history=make_history()+[
                Message(
                    role="assistant",
                    tool_calls=[ToolCall(id="c1",name="get_weather",arguments={"city":"北京"})]
                ),
                Message(role="tool",content="北京天气晴，28摄氏度")
            ]
    mock.chat(make_history(),[])
    mock.chat(history,[])
    assert len(mock.calls)==2

def test_改变列表后测试不受影响():
    mock=MockProvider(make_script())
    history=make_history()
    mock.chat(history,[])
    history.append(Message(role="user",content="我想查询广州的天气"))
    assert len(mock.calls[0])==2
