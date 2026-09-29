from openai import OpenAI
from .models import Message,ToolCall
class OpenaiClient:
    def __init__(self,model:str,api_key:str,base_url:str,):
        self.model=model
        self.client=OpenAI(api_key,base_url)
    def generate(self,messages:list[Message]):
        print("正在调用大语言模型...")
        api_messages=[]
        for message in messages:
            api_message=[
                {"role":message.role,"content":message.content}
            ]
            if message.tool_calls:
                api_message["tool_calls"]=[
                    {
                        "id":tool_call.id,
                        "type":function,
                        "function":{
                            "name":tool_call.Name,
                            "argument":tool_call.argument
                        }
                    }
                    for tool_call in tool_calls
                ]
            if message.tool_calls_id:
                api_message["tool_calls_id"]=message.tool_calls_id
            api_messages.append(api_message)
        try:
            response=self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                stream=False
            )
            answer=response.choices[0].message.content
            print("大模型响应成功")
            return answer
        except Exception as e:
            return f"调用LLM时发生错误"