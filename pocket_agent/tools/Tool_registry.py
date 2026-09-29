from .base import Tool
class ToolRegistry:
    def __init__(self):
        self.tools:dict[str,Tool]={}
#将工具登记进去
    def 