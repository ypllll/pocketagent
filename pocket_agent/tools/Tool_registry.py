from .base import Tool
from pocket_agent.models import ToolResult
class ToolRegistry:
    def __init__(self):
        self.tools:dict[str,Tool]={}
#将工具登记进去
    def register(self,tool:Tool)->None:
        self.tools[tool.name]=tool
#按名字查工具
    def get_tool(self,name:str)->Tool|None:
        return self.tools.get(name)
#返回所有工具名
    def tools_name(self)->list[str]:
        return list(self.tools)
#生成模型能够看得懂的工具列表
    def definitions(self)->list[dict]:
        return [self.tools[name].schema() for name in sorted(self.tools)]
#执行,要检查模型传回的这个工具是否存在，参数是否合法，执行时是否异常，
#且无论成功与否，都要返回ToolResult，然后回填给模型
    def execute(self,name:str,arguments)->ToolResult:
        tool=self.get_tool(name)
        #工具是否存在
        if tool is None:
            available=self.tools_name()
            return ToolResult(
                content=f"未定义工具，{available}为可用工具\n请根据上面的错误换一个思路，请勿重复调用",
                is_error=True
            )
        #传入参数是否合法
        error=tool.validate(arguments)
        if error:
            return ToolResult(
                content=f"传入工具的参数错误，错误为{error}\n请根据上面的错误换一个思路，请勿重复调用",
                is_error=True
            )
        #工具调用过程中是否出错
        try:
            return tool.execute(**arguments)
        except Exception as e:
            return ToolResult(
                content=f"执行工具过程中出错了，错误类型为：{e}\n请根据上面的错误换一个思路，请勿重复调用",
                is_error=True
            )
        
        