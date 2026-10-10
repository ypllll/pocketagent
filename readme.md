1.整体学习路径概述
在过去的一段时间呢，我先是快速的学习完了发布的28天学习计划，因为我之前有过python的基础，所以前21天的知识我学的很快，把python重要的知识点都再回顾了一遍。然后就正式的进入了学习agent的阶段，我选的是A线-跟着GitHub上一个叫做Learn-Claude-Code的开源项目学习，这的确是一个蛮好的项目，他让我懂得了agent的基本运行逻辑，如整体框架Loop；tool；上下文context；context怎么被四步压缩；subagent：agent在遇到很大的任务时，会让子agent来做然后返回给他最终结果，防止上下文爆了；skill和hook等等概念知识。但是当我学习完这些概念知识的时候，我感觉我还是只停留在表面，对他们的底层逻辑是怎么运行的还是一头雾水，于是，我便想做一个agent，这样我对agent的底层逻辑会更加清楚，接下来我会介绍我近期做的这个项目————pocketagent。这个项目我也上传到了GitHub上面，路径是————https://github.com/ypllll/pocketagent.git

2.对pocketagent项目的介绍
首先，我参考了开源智能体项目nanobot的架构设计，并结合我自己的想法，开发了pocketagent————这是一个智能客服agent，是一个轻量级的AIagent项目。这个项目在实际的作用，就是你可以把某个产品的说明书，退货流程等等文件丢给他，然后我是把RAG的检索功能封装成了一个工具，这样你把所有的文件扔进去了之后，就可以通过这个工具进行检索，然后把检索到的块返回给模型，这样模型在每次接受到用户的问题时，就不用每次都把整个产品说明书和退货流程读一遍，而是通过我写好的那个工具直接检索出最相关的某三个块，然后和用户的问题一起交给大模型，这样我认为会更加省时，省token，同时精确度更高。
    2.1技术架构
    以下是我的pocketagent项目的整体框架：
    pocket_agent/
    │
    ├── __init__.py
    ├── models.py                    数据结构：Message / ToolCall / ToolResult
    │                                / LLMResponse / Runresult / TraceStep
    │
    ├── runtime/                     ① Agent 运行时
    │   ├── __init__.py
    │   └── loop.py                   AgentRuntime：多步循环、停止条件、错误处理
    │
    ├── providers/                   ② 模型适配
    │   ├── __init__.py
    │   ├── base.py                   Provider 抽象基类（chat 接口 + name 属性）
    │   ├── openai_provider.py        DeepSeek 实现（OpenAI 兼容）
    │   └── mockprovider.py           Mock 实现（按剧本返回，供测试用）
    │
    ├── tools/                       ③ 工具系统
    │   ├── __init__.py
    │   ├── base.py                   Tool 基类：schema() / validate() /execute()
    │   ├── Tool_registry.py          ToolRegistry：注册 + 三关口校验 + 错误转换
    │   ├── search_documents.py       工具① 检索知识库（封装 Retriever）
    │   ├── query_order.py            工具② 查询订单（假数据 + 模拟错误）
    │   └── create_ticket.py          工具③ 创建工单（写入 SQLite）
    │
    ├── documents/                   ④ RAG 流水线
    │   ├── __init__.py
    │   ├── loaders.py                PDF / TXT / MD → 纯文本
    │   ├── chunker.py                长文本 → chunk（带 source / index 元数据）
    │   ├── embedder.py               Embedder 抽象基类
    │   ├── SiliconFlowEmbedder.py    硅基流动实现（bge-m3，1024 维）
    │   ├── vector_store.py           ChromaDB 封装：add_chunks / search / count
    │   ├── reranker.py               硅基流动 rerank 接口（bge-reranker-v2-m3）
    │   ├── retriever.py              Retriever：召回 + 重排两阶段
    │   └── ingest_document.py        入库入口：路径 → 解析 → 切块 → 入库
    │
    ├── observability/               ⑤ 可观测性
    │   ├── __init__.py
    │   └── trace.py                  TraceRecorder：记录模型/工具调用与耗时
    │
    └── session/                     ⑥ 会话持久化
        ├── __init__.py
        └── manager.py                SessionManager：对话历史的读写
    2.2项目理解
    本项目百分之九十的代码是由我手写完成，除了systemprompt和streamlit前端展示界面由codex完成。不过，未来是AI的时代，我手写代码的目的其实也只是为了更好理解agent底层的运作逻辑，毕竟这也是我第一次接触agent。
    不过有些东西，我认为是只有亲手写过，亲手debug过才会理解的更深刻：
    我在这里还是想写一下整个loop的流程吧，因为其实我的pocketagent有这么多模块，他们都被封装好了，最终不过都是在loop这里外显了，所以呢，讲通我这个loop的流程，其实也就讲通了我的整个项目。

    ###首先呢，就是先组装最初的消息，也就是systemprompt和用户输入：
```python
    messages = [
        Message(role="system", content=SYSTEM_PROMPT),
        Message(role="user", content=user_input),
    ]
```
    systemprompt很关键，因为当你开发某个具体领域的agent时，写好systemprompt，就是定好了他的角色和边界，例如下次我想做一个金融分析agent，那我就要重写一套systemprompt，就是给agent换一个人设。然后就正式进入循环了，这里很关键的一点是要定一个max_step，也就是最大循环次数，防止agent无限次循环下去，在这里我定的max_step是8。

    ###第二步就到了调用模型了，我在providers这个module里面已经写好了一个openai的接口，因为我打算调的是deepseek的api，他兼容openai的接口规范，然后这个接口文件我命名为openai_provider.py，这个接口的作用就是把大模型传回来的信息整理好，存到我在model这个module里面定义的一个数据结构叫做LLMresponse，我的LLMresponse如下：
```
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
```
    就是把大模型返回的那些json数据里面的content，tool_calls等等信息提取出来，放到我的这个LLMresponse的数据容器里面。当然我这个provider还有其他的作用，就是把我内部的Messgae对象转成API认识的dict格式

    ###第三步是记录这一步，也就是trace，调用大模型如果不记录的话，将来测试这个agent的时候，可观测性就会很差，就是说不写trace的话，你就只能看到问题和答案，中间发生什么你完全不知道，比如说有时工具失败了但模型依旧回答的很好，这样错误就会被掩盖。不过我目前的trace功能还是比较简陋的，只记录了：
    模型调用方面：这是第几轮，用的哪个模型，耗时多少以及模型为什么停下
    工具调用方面：这是第几轮，用了哪个工具，耗时多少，传入的参数以及返回结果
    但是还不能记录token的消耗，发给模型的完整上下文。

    ###第四步是把模型回答加进历史，我的总历史是在一个命名为messages的列表里面：
```
    messages.append(Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls
            ))"""
```
    也就是把大模型回答的信息保存到我的Message数据结构里面然后再追加到总历史messages里面
    Message数据容器如下：
    """@dataclass
    class Message:
        role:str
        content:str|None=None
        tool_calls:list[ToolCall]=field(default_factory=list)
        tool_call_id:str|None=None
    里面存放的信息有对象，内容，工具调用信息和对应的序号。

    ###第五步就是判断要不要调用工具，这也是结束条件之一，然后我的LLMresponse这个数据容器里面有一个方法是（should_execute_tools），这个方法就是专门用来判断是否要调用工具的。如果不用调用工具，那就直接return Runresult，Runresult也是我写在models这个module的一个数据容器，Runresult数据容器如下：
```
    @dataclass
    class Runresult:
        answer:str|None
        stop_reason:str#completed,error,timeout
        message:list[Message]
        trace:list[TraceStep]=field(default_factory=list)
```
    这个数据容器会记录最终返回给用户的回答，结束原因和总历史，以及每次的trace。

    ###第六步就是执行工具，如果在上一步判断出来有tool_call，那么就需要执行工具。执行工具的代码是：
    result = self.tools.execute(tool_call.name, tool_call.arguments)
    不过这个execute方法是在ToolRegistry里面的，也就是一个工具表，所以说，在具体实现的过程中，我的工具是在更里面一层，直接出现在loop里面的是我的工具表，我要先把我的tools注册到工具表里面。然后execute这个方法具体就是检查大模型传回来的工具，大模型可能回传回来多个工具的，所以这里也用了for循环，具体检查的有三道关卡：
    1.工具存在吗（模型是有幻觉的，他可能会传回来一个不在我的工具表里面的工具）
    2.传入工具的参数合法吗（这个具体实现就是在工具的父类里面了，在tools文件夹里面的base文件，里面的validate方法就是具体实现怎么检查传入工具是否合法的）
    3.执行时报错吗（用try/except兜住，防止直接报错）
    ToolRegistry还有一个重要的作用就是把所有工具的schema拼成一个数组

    ###第七步是把工具结果回填，当然再次之前还要记录工具调用的trace，不过这个我在上面的模型调用时已经一起说明了，回填的具体代码是：
```
    messages.append(Message(
                    role="tool",
                    content=result.content,
                    tool_call_id=tool_call.id
                ))
```
    这个tool_call_id其实挺重要的，因为模型一次可能会返回多个工具的，所以需要一个编号让他们彼此对应。

    ###ok最后一步就是要有一个步数用尽的兜底：
```
    return Runresult(
            answer="步数用尽，没能在规定循环内完成任务",
            stop_reason="max_iterations",
            message=messages,
            trace=traces.steps
        )
```
    因为如果没有这个兜底的话，循环结束后就会返回None，用户就什么都收不到了
    ok，这大概就是我这个项目的大概了，不过其中还有很多实现细节被封装起来了，不过下面我还想展示我在这个项目中用到的一个很重要的技术————RAG

3.对RAG的理解
    3.1.RAG的完整流程
    RAG的工作流程在我的documents文件夹里面，整体流程如下：
    documents/ 
    ① 解析     loaders.py         PDF/TXT/MD → 纯文本
    ② 切块     chunker.py         长文本 → chunk（带 source / index 元数据）
    ③ 向量化   embedder.py        文本 → 1024 维向量（bge-m3）
    ④ 存储     vector_store.py    向量 + 原文 + 元数据 → ChromaDB
    ⑤ 检索     retriever.py       两阶段：
                                ├─ 召回：向量相似度取 top 10
                                └─ 重排：reranker 精排取 top 3
    言简意赅地说：RAG工作流程就是先把导入的文件转换成纯文本，然后再将这个长文本切块，切成一个个chunk，然后再将这些chunk向量化，再将这些向量放到一个向量数据库里面。然后当用户输入完他的问题时，要将用户输入的问题也向量化，然后要经过两阶段的检索，第一阶段的检索是召回，通过计算向量相似度取出与用户问题最相似的前十个chunk，然后再经过一个reranker重排的步骤，最终取出与用户问题相似度最高的三个chunk，把这三个chunk和用户的问题打包传给大模型。
    3.2.RAG与pocketagent项目的关联
    因为我是想要做一个智能客服助手，所有说如果我只用RAG是不够的，因为我还需要其他的tools，比如说用户想要查询订单信息，比如说用户要求转人工，这样我就需要让RAG的检索功能与其他tool一起合作，所以说我就把RAG的检索功能包装成了一个tool，让他与其他两个工具一起配合工作。
        3.2.1.多工具协同
        因为codex帮我写了streamlit展示界面，所以说我可以通过这个前端网页来测试他们多工具协同的能力，下面有一个我让他们三个工具协同工作的案例，因为我无法上传图片，所以我让codex帮我根据实验结果整理成了文字版：
        ### 3.2.1 多工具协同的实际案例

        **提问**

        > 订单 ORD-5678 能退货吗？如果不能，帮我转人工

        **最终回答**

        > 工单已创建成功：
        >
        > - **工单号**：TK-20261010-001
        > - **优先级**：一般
        > - **状态**：待处理
        >
        > 人工客服会在 24 小时内与您联系。如果您希望更快处理，也可以补充说明退货的具体原因（例如是否存在质量问题），我会帮您一并补充到工单里。

        **执行轨迹**

        ```
        总耗时：5619 ms ｜ 3 次工具调用

        step:1  model  deepseek-chat  2151 ms   finish_reason: tool_calls
        step:1  tool   query_order       0 ms   {"order_id": "ORD-5678"}
                        返回：订单ORD-5678 商品iPhoneDuo 标准版 256GB 状态已签收 签收日期：2026-09-20
        step:1  tool   search_documents 657 ms  {"query": "退货政策 退货期限 除外情形"}
                        返回：[资料1] 来源：iPhoneDuo_产品说明书.pdf 第24块
        step:2  model  deepseek-chat  2049 ms   finish_reason: tool_calls
        step:2  tool   create_ticket    10 ms   {"issue": "订单 ORD-5678（iPhoneDuo 标准版 256GB），
                                                签收日期 2026-09-20，距今 20 天。用户…"}
        step:3  model  deepseek-chat   752 ms   finish_reason: stop
        ```

        **检索到的资料**

        | 编号 | 来源文件 | 位置 |
        | --- | --- | --- |
        | 资料 1 | iPhoneDuo_产品说明书.pdf | 第 24 块 |
        | 资料 2 | iPhoneDuo_产品说明书.pdf | 第 13 块 |
        | 资料 3 | iPhoneDuo_产品说明书.pdf | 第 26 块 |
        这也是我认为我的pocketagent这个项目一个比较两眼的地方，就是它实现了多工具协同

4.总结与不足
这个项目虽然比较简易，但通过这个项目，之前那些看起来很浮于表面的名词，像什么loop，tool，RAG等等，我理解了他们底层的逻辑，举一个例子：
比如Tool Calling，自己写完之后才知道背后有一套完整的消息协议——assistant先声明 tool_calls，每个都要有id，工具结果必须用tool_call_id配对回填，顺序错了API直接报错
当然我也知道我距离一个成熟的agent还差很多，比如说context，memory等等，这些我都还没有实现，不过也是因为时间的确不够，不过我将会在下一段时间里面把这些知识都学习完整，下一步我打算先做session持久化，因为写context和memory都需要一个地方来读历史，一步步丰盈我的这个pocketagent，让pocketagent成为一个更加成熟的agent，同时也让自己学到更多。

