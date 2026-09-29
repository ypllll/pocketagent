from .base import Tool
from pocket_agent.models import ToolResult
class get_weather(Tool):
    name="get_weather"
    description="查询不同城市的天气"
    parameters={
        "type":"object",
        "properties":{
            "city":{"type":"string","description":"要填一个城市名"}
        },
        "required":["city"]
    }
    _FAKE_DATA = {"北京": ("晴", 28), "上海": ("小雨", 24), "广州": ("多云", 31)}
    def execute(self,city:str)->ToolResult:
        if city not in self._FAKE_DATA:
            return ToolResult(content="没有目标城市",is_error=True)
        weather,temp=self._FAKE_DATA[city]
        return ToolResult(content=f"{city}今天的天气是{weather},温度是{temp}")
