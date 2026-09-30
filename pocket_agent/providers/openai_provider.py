from pocket_agent.models import Message,LLMResponse,ToolCall
from pocket_agent.providers.base import Provider
import json
from openai import OpenAI
from dotenv import load_dotenv
import os
def message_to_api_dict(message:Message)->dict:
    api_message={"role":message.role}
    if message.content is not None:
        api_message["content"]=message.content
    if message.tool_calls:
        api_message["tool_calls"]=[]
        for tool_call in message.tool_calls:
            api_message["tool_calls"].append({
                "id":tool_call.id,
                "type":"function",
                "function":{
                    "name":tool_call.name,
                    "arguments":json.dumps(tool_call.arguments,ascii=False)
                }
            })
    if message.role=="tool":
        api_message["tool_call_id"]=message.tool_call_id
    return api_message

class OpenaiProvider(Provider):
    def __init__(self,model:str,api_key:str,base_url:str):
        self.model=model
        self.client=OpenAI(api_key=api_key,base_url=base_url)
    @classmethod
    def from_env(cls)->"OpenaiProvider":
        load_dotenv()
        model=os.getenv("MODEL_ID")
        api_key=os.getenv("DEEPSEEK_API_KEY")
        base_url=os.getenv("BASE_URL")
        return cls(model=model,api_key=api_key,base_url=base_url)

    def chat(self,messages:list[Message],tools:list[dict])->LLMResponse:
        api_messages=[]
        for message in messages:
            api_messages.append(message_to_api_dict(message))
        if tools:
            response=self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                tools=tools
            )
        else:
            response=self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                tools=None
            )
        llmresponse=LLMResponse()
        tool_calls=[]
        for call in (response.choices[0].message.tool_calls or []):
            tool_calls.append(
                ToolCall(
                    id=call.id,
                    name=call.function.name,
                    arguments=json.loads(call.function.arguments)
                )
            )
        llmresponse.tool_calls=tool_calls
        llmresponse.content=response.choices[0].message.content
        llmresponse.finish_reason=response.choices[0].finish_reason
        llmresponse.usage=response.usage.total_tokens if response.usage else None
        return llmresponse

