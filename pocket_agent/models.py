from dataclasses import dataclass,field
@dataclass 
class ToolCall:
    id:str
    name:str
    arguments:dict

@dataclass
class ToolResult:
    content:str
    is_error:bool=False

@dataclass
class Message:
    role:str
    content:str|None=None
    tool_calls:list[ToolCall]=field(default_factory=list)
    tool_call_id:str|None=None

@dataclass
class LLMResponse:
    content:str|None=None
    tool_calls:list[ToolCall]=field(default_factory=list)
    finish_reason:str="stop"#tool_call,stop,length
    usage:int|None=None
    @property
    def should_execute_tools(self)->bool:
        if not self.tool_calls:
            return False
        if self.finish_reason not in["tool_calls","function_call","stop"]:
            return False
        return True
    
@dataclass
class RunSpec:
    messages:list[Message]
    tools:list[ToolCall]
    max_steps:int=8
    timeout_s:float|None=None

@dataclass
class TraceStep:
    step:int#第几轮
    kind:str#model,tool
    name:str#模型或工具的名字
    elapsed_ms:int#耗时
    is_error:bool=False#是否出错
    detail:str=""#补充finishreaon,结果摘要

@dataclass
class Runresult:
    answer:str|None
    stop_reason:str#completed,error,timeout
    message:list[Message]
    trace:list[TraceStep]=field(default_factory=list)