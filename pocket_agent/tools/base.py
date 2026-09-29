from abc import ABC,abstractmethod
from pocket_agent.models import ToolResult
_TYPE_MAP = {
    "string":  (str,),
    "integer": (int,),
    "number":  (int, float),
    "boolean": (bool,),
    "array":   (list,),
    "object":  (dict,),
}
class Tool(ABC):
    name:str=""
    description:str=""
    parameters:dict={
        "type":"object",
        "properties":{}
    }
    #有不能生的参数时要写上required=[]
    @abstractmethod
    def execute(self,**kwargs)->ToolResult:
        ...
    def schema(self)->dict:
        """把这个工具翻译成openai需要的格式"""
        return {
            "type":"function",
            "function":{
                "name":self.name,
                "description":self.description,
                "parameters":self.parameters
            }
        }
    def validate(self,arguments:dict)->list[str]:
        """返回错误信息列表,空列表等于通过"""
        error:list[str]=[]
        properties=self.parameters.get("properties",{})
        for key in self.parameters.get("required",[]):
            if key not in arguments:
                error.append(f"缺少必填参数{key}")
        for key,value in arguments.items():
            if key not in properties:
                error.append(f"未知参数{key}")
                continue
            expected=properties[key].get("type")
            allowed=_TYPE_MAP.get(expected)
            if allowed is None:
                continue
            if expected in ["number","integer"] and isinstance(value,bool):
                error.append(f"参数{key}正确类型应该为{expected},收到bool")
            elif not isinstance(value,allowed):
                error.append(f"参数{key}正确类型应该为{expected},收到{type(value).__name__}")
        return error
