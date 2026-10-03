# 04 Agent Runtime

状态：2.2-A / 2.2-B 学习完成（2026-09-22），Day 1 起开始实现。

证据分级：【源码确认】= 已读 `reference/nanobot`（commit `8eea1cb`）；【官方文档】；【设计建议】；【待验证】。
本文引用的行号来自该 commit，行号可能随上游变化。

## 1. 两个角色的边界

### 1.1 厨师收到的"任务单"：【源码确认】`nanobot/agent/runner.py` L88-117

`AgentRunSpec` 共 24 个字段，分为四组：

| 分组 | 字段 | 作用 |
| --- | --- | --- |
| 干活的家伙什 | `tools`、`runtime`、`max_iterations`、`max_tool_result_chars`、`concurrent_tools` | 能用哪些工具、用哪个模型、最多几轮、单条结果上限、是否并发 |
| 这一桌的原料 | `transcript_input`、`transcript_builder`、`initial_messages`、`workspace`、`session_key`、`provider_state` | 历史原料 + 组装说明书 + 会话标签 |
| 回调（向服务员求助） | `injection_callback`、`terminal_injection_callback`、`continuation_callback`、`checkpoint_callback` | 检查插话、存进度 |
| 开关与收尾 | `hook`、`finalize_on_max_iterations`、`error_message`、`max_iterations_message`、`consolidate_history`、`events` | 插桩、上限收尾、错误文案、事件出口 |

要点：`workspace`（路径）与 `session_key`（标签）**不是**访问会话档案的把手；会话档案由 `SessionManager` 持有，只在 Loop 侧。Runner 因此**无法**自行读数据库或配置——不是约定，是拿不到。

### 1.2 厨师交回的"体检报告"：【源码确认】`runner.py` L118-139

`AgentRunResult` 的关键字段：`final_content`、`messages`、`tools_used`、`usage`、`round_usages`、`stop_reason`、`error`、`failure_error_kind`、`tool_events`、`had_injections`、`provider_state`。

注意：返回的是结构化结果，不是一段打印文本。

### 1.3 交接员：【源码确认】`nanobot/agent/loop.py` L2077 `_run_turn`

`_run_turn` 只做三件事：告知投递层"开始运行"（L2081）、`await self._run_agent_loop(...)`、把 `result` 的字段抄回 `ctx`（`final_content` / `all_messages` / `stop_reason` / `usage` 等），并把 `round_usages` 记入投递层。

## 2. 一条消息的旅程

### 2.1 七阶段调度：【源码确认】`loop.py` `_process_message`（L1697，阶段调用在 L1785-1792）

```
restore → compact → command（若处理完则 return）→ build → run → save → respond
```

| 阶段 | 作用 | 对应旅游助手 |
| --- | --- | --- |
| restore | 取回会话档案 | 无 |
| compact | 需要时压缩历史 | 无 |
| command | 命令类消息短路处理 | 无 |
| build | 取历史、拼 transcript、提前落盘用户消息 | 部分（L95-98） |
| run | 交给 Runner | 是（L102-137） |
| save | 持久化本轮 | 无 |
| respond | 决定给用户回什么 | 部分（print） |

### 2.2 build 阶段：【源码确认】`loop.py` `_build_turn`（L1968 起）

三件事：`session.get_history(...)` 取历史；`_persist_user_message_early(...)` **在调模型之前**落盘用户消息；`_build_transcript_input(ctx)` 打包原料。

### 2.3 交任务单：【源码确认】`loop.py` 约 L1220

`AgentRunSpec(initial_messages=None, tools=..., transcript_input=..., transcript_builder=..., hook=..., concurrent_tools=True, checkpoint_callback=_checkpoint, injection_callback=_drain_pending, terminal_injection_callback=_wait_for_pending, continuation_callback=_goal_continue, finalize_on_max_iterations=..., events=...)` 然后 `await self.runner.run(...)`。

设计含义：不给现成 messages，给"原料 + 说明书"，因为"是否压缩、是否插入新消息"只有下锅前才知道。

## 3. 主循环骨架：【源码确认】`runner.py::_run_core`

```
for iteration in range(spec.max_iterations):        # L423
    排空中途插话（每次模型调用前）
    hook.before_iteration(...)
    构建本轮请求（可能触发压缩）
    response, usage = await self._request_model(...)
    if response.should_execute_tools:               # L478
        落 assistant 消息 → 检查点 awaiting_tools
        results = await execute_tool_calls(...)     # 可并发
        每条结果 → role="tool" + tool_call_id 回填
        检查点 tools_completed
        continue
    # 无工具调用：处理空回复 / 截断 / 错误，然后 break
else:
    stop_reason = "max_iterations"                  # L786
    if spec.finalize_on_max_iterations:
        不带工具再问一次，要收尾
    要不到 → 兜底文案
```

工具执行门控：【源码确认】`nanobot/providers/base.py` 约 L613：

```python
return self.finish_reason in ("tool_calls", "function_call", "stop")
```

即：**不仅看有没有 tool_calls，还要看结束原因**。`length`（参数可能被截断）、`refusal` / `content_filter`（拒答产生的假工具调用）、`error` 都不执行。

## 4. 五种停止方式

| stop_reason | 触发 | 源码位置 | 行为 |
| --- | --- | --- | --- |
| `completed` | 正常拿到最终文本 | 循环初始值；正常分支 break | 追加 assistant 消息后结束 |
| `max_iterations` | for 循环走完未 break | L786 起的 `else:` 分支 | 先不带工具再问一次（`_request_no_tools`，`tools=None`），要不到用 `_max_iterations_fallback` |
| `error` | `response.finish_reason == "error"` | L708-715 | 欠费专用文案 `_ARREARAGE_ERROR_MESSAGE` 或通用文案；补占位消息 |
| `empty_final_response` | 内容空白且重试耗尽 | L731-735 | 写入 `EMPTY_FINAL_RESPONSE_MESSAGE` |
| `cancelled` | `asyncio.CancelledError` | L286 | 标记后原样抛出 |

两组"继续而非停止"的机制（【源码确认】）：空回复重试上限 `_MAX_EMPTY_RETRIES = 2`（L72）、长度截断续写上限 `_MAX_LENGTH_RECOVERIES = 3`（L73）。

## 5. 三条异常路径

| 路径 | 处理方式 | 证据 |
| --- | --- | --- |
| 模型调用失败 | Provider 把异常**转成带 `finish_reason="error"` 的响应对象**，Runner 按数据分支处理（不是到处 try/except） | `providers/base.py` `_error_response_from_exception`；`runner.py` L708 |
| 工具执行失败 | `ToolRegistry.execute` 捕获异常 → `ToolResult.error("Error executing {name}: ...")`，并追加提示 `[Analyze the error above and try a different approach.]`，作为工具回执回填 | `tools/registry.py` L192-201；`tools/execution.py` L23 |
| 钩子/回调失败 | 记日志、不中断主流程（`on_finally` 失败会记 `AgentHook.on_finally error after ...`） | `runner.py::run` 的 finally 分支 |

共性：**错误被"数据化"成模型或调用方能读懂的东西**，而不是靠异常层层上抛。

## 6. 结果流向

```
AgentRunResult
  → _run_turn 抄回 ctx（loop.py L2095-2110，记录 round_usages）
  → _persist_turn（L2117）：空内容补 EMPTY_FINAL_RESPONSE_MESSAGE；写 session.metadata["_last_usage"]（L2139）
  → _save_turn（L2243）
  → _prepare_outbound（respond 阶段）
  → delivery.complete(response)（_dispatch_one，L1557）
```

## 7. 与旅游助手逐项对照

| 旅游助手 | nanobot | 差别 |
| --- | --- | --- |
| L92 建客户端（模块级） | 组合根 + 依赖注入 | 配置不写死，对象外部创建 |
| L93 系统提示词 | ContextBuilder | 身份 + 项目说明 + 记忆 + 技能 |
| L94 `input()` | 通道 + 收件箱 | 多来源、可并发 |
| L95-98 手写 messages | `session.get_history` + transcript 组装 | 从档案取料 |
| L99-100 `max_step` | `AgentRunSpec.max_iterations` | 参数由外部传入 |
| L103-106 超步数硬停 | `for ... else:` + 收尾 + 兜底文案 | 不让用户面对空白 |
| L107-111 调模型（无保护） | `_request_model` + 重试 + 流式 + 错误分类 | 失败可恢复 |
| L114 只看 tool_calls | `should_execute_tools`（双信号） | 防截断/拒答误执行 |
| L117-131 串行分发 | `execute_tool_calls`（可并发）+ 参数校验 | 更安全、更快 |
| L133-137 回填（正确） | 同左 + 结果裁剪 | 加预算保护 |
| 无 | `AgentRunResult` / usage / tool_events | 结构化可观测 |

## 8. 对 PocketAgent 的取舍【设计建议】

### V1 必须做

1. 消息契约：四条 role 规则 + `tool_call_id` 配对（协议强制）。
2. 双信号判断是否执行工具：有 `tool_calls` **且** `finish_reason` 允许。
3. 步数上限，且用尽时给出**用户可读的结果**（`stop_reason="max_iterations"` + 固定文案），不是静默退出。
4. 工具错误转成可读回执回填，循环不崩。
5. `RunResult` 结构化：`answer` / `stop_reason` / `usage` / `trace`。
6. Runtime 只依赖接口（Provider / ToolRegistry / 存储），保证可用 Mock 单测。

### V1 可选（时间允许）

1. 空回复重试 1 次。
2. 长度截断续写 1 次。
3. 每轮消息落盘（不做完整断点恢复）。
4. 工具并发（工具少时收益低，先串行）。

### V2 再做

注入（中途插话）、长度续写链、provider 原生压缩、完整会话恢复、多 Provider 重试矩阵、完整 Hooks 生命周期、MessageBus 与多渠道。

## 9. 待验证

1. `ContextGovernor` 的裁剪与压缩细节（Day 9-12 再读）。
2. `RecoveryCoordinator` 的恢复机制。
3. Provider 重试矩阵与错误分类的完整闭环。
4. 流式相关字段（`pending_stream_content`）的边界行为。
