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
class Runresult:
    answer:str|None
    stop_reason:str#completed,error,timeout
    message:list[Message]