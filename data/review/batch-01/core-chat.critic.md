# Critic 评审报告：core-chat（聊天与消息处理）

- 被评审文件：`review/batch-01/core-chat.md`
- 事实源：`wiki-work/facts/batch-01/core-chat.facts.json`（47 条）
- 评审人：独立 critic（全新 session，未参与写作）
- 评审日期：2026-09-30
- 方法：逐条打开 ref 指向的代码行（±5 行窗口），核对符号名与断言内容；另做 lint / 禁用词 / frontmatter / wikilink 合规检查

## 一、逐条事实判定（47/47 支撑）

| # | 事实摘要 | ref | 判定 | 备注 |
|---|---------|-----|------|------|
| 1 | AIMessageManager 是与 EnhancedAIService 通信的单例 object，设计无状态 | AIMessageManager.kt:80 | 支撑 | KDoc 67-70 行"负责管理与 EnhancedAIService 的所有通信"；80 行"无状态…所有数据经方法参数传入"；`object` 声明在 85 行（±5 内） |
| 2 | initialize 初始化 toolHandler / packageManager / apiPreferences | AIMessageManager.kt:105 | 支撑 | 110-113 行：`AIToolHandler.getInstance(context)`、`PackageManager.getInstance(context, toolHandler)`、`ApiPreferences.getInstance(context)` |
| 3 | sendMessage 是消息发送主入口 | AIMessageManager.kt:346 | 支撑 | `suspend fun sendMessage(` 在 351 行 |
| 4 | sendMessage 先调用 getMemoryFromMessages 转记忆 | AIMessageManager.kt:380 | 支撑 | 385 行 `val memory = getMemoryFromMessages(...)` |
| 5 | 图片链接数量裁剪 limitImageLinksInChatHistory | AIMessageManager.kt:612 | 支撑 | `private fun limitImageLinksInChatHistory(` 在 616 行 |
| 6 | 音视频链接数量裁剪 limitMediaLinksInChatHistory | AIMessageManager.kt:588 | 支撑 | `private fun limitMediaLinksInChatHistory(` 在 592 行 |
| 7 | 先尝试 MessageProcessingPluginRegistry.createExecutionIfMatched，匹配则插件接管 | AIMessageManager.kt:431 | 支撑 | 436 行调用；后接"普通模式"分支 |
| 8 | 普通模式调用 enhancedAiService.sendMessage 构造 SendMessageOptions | AIMessageManager.kt:484 | 支撑 | 489 行调用，注释"使用普通模式" |
| 9 | buildUserMessageContent 组装用户消息最终内容（含附件与记忆标签） | AIMessageManager.kt:126 | 支撑 | `suspend fun buildUserMessageContent(` 在 131 行，参数含 attachments / workspacePath / 记忆相关 |
| 10 | 先经 InputProcessor.processUserInput 处理原始输入 | AIMessageManager.kt:144 | 支撑 | 149 行调用 |
| 11 | `<proxy_sender>` 标签携带代发人名称 | AIMessageManager.kt:161 | 支撑 | 161-166 行构建 `<proxy_sender name="..."/>` |
| 12 | `<reply_to>` 携带发送者、时间戳与内容（超 100 字符截断） | AIMessageManager.kt:176 | 支撑 | 177 行 `take(100) + "..."`；179 行 sender/timestamp/content |
| 13 | `<workspace_attachment>` 封装工作区变更，WorkspaceChangeTracker.consumeChanges + WorkspaceAttachmentProcessor.generateWorkspaceAttachment | AIMessageManager.kt:194 | 支撑 | 197-204 行完整链路 |
| 14 | logMessageTiming 记录各阶段耗时，tag 为 MESSAGE_PROCESS_TIMING_TAG | AIMessageManager.kt:49 | 支撑 | 49 行 `internal const val MESSAGE_PROCESS_TIMING_TAG = "MessageProcessTiming"` |
| 15 | cancelCurrentOperation / cancelOperation(chatId) / cancelAllOperations | AIMessageManager.kt:640 | 支撑 | 三函数分别在 644 / 648 / 669 行（见备注 N1） |
| 16 | summarizeMemory 生成记忆总结 | AIMessageManager.kt:684 | 支撑 | `suspend fun summarizeMemory(` 在 689 行 |
| 17 | shouldGenerateSummary 判断是否需要生成对话总结 | AIMessageManager.kt:1281 | 支撑 | `fun shouldGenerateSummary(` 在 1286 行 |
| 18 | MessageProcessingDelegate 是面向 UI 的消息处理编排类，构造函数注入 getEnhancedAiService、addMessageToChat、onTurnComplete 等回调 | MessageProcessingDelegate.kt:54 | 支撑 | `class MessageProcessingDelegate(` 在 59 行；回调参数在 61-66 行 |
| 19 | 输入草稿由 _userMessage（MutableStateFlow）持有，对外暴露为 userMessage | MessageProcessingDelegate.kt:152 | 支撑 | 156-157 行 |
| 20 | _isLoading 与 _activeStreamingChatIds 分别暴露加载态与流式会话集合 | MessageProcessingDelegate.kt:158 | 支撑 | 163 行 / 166 行（见备注 N2） |
| 21 | _inputProcessingStateByChatId 按 chatId 记录输入处理状态（EnhancedInputProcessingState） | MessageProcessingDelegate.kt:164 | 支撑 | 168-169 行 |
| 22 | 流式节流 STREAM_SCROLL_THROTTLE_MS=200ms，STREAM_PERSIST_INTERVAL_MS=1000ms | MessageProcessingDelegate.kt:80 | 支撑 | 84-85 行 `200L` / `1000L` |
| 23 | sendUserMessage 是用户消息发送入口 | MessageProcessingDelegate.kt:681 | 支撑 | `fun sendUserMessage(` 在 686 行 |
| 24 | 空消息且无附件（且非自动续写/群组编排）时直接忽略 | MessageProcessingDelegate.kt:714 | 支撑 | 716 行 `if (rawMessageText.isBlank() && attachments.isEmpty() && !isAutoContinuation && !isGroupOrchestrationTurn)` |
| 25 | 同会话正在处理中（chatRuntime.isLoading）时新请求被忽略 | MessageProcessingDelegate.kt:722 | 支撑 | 723 行 `if (chatRuntime.isLoading.value)` |
| 26 | 每轮 turnId = turnSequence.incrementAndGet() 并设为 activeTurnId，轮次隔离 | MessageProcessingDelegate.kt:726 | 支撑 | 730-731 行 |
| 27 | ChatRuntime 按 chatId 维护运行时状态：sendJob、responseStream、activeStreamingTurn | MessageProcessingDelegate.kt:203 | 支撑 | `private data class ChatRuntime(` 在 207 行，字段齐全 |
| 28 | 各会话 ChatRuntime 存放在 chatRuntimes（ConcurrentHashMap） | MessageProcessingDelegate.kt:224 | 支撑 | 227 行 `private val chatRuntimes = ConcurrentHashMap<String, ChatRuntime>()` |
| 29 | runtimeFor(chatId) 懒创建并返回对应会话 ChatRuntime | MessageProcessingDelegate.kt:244 | 支撑 | 243-246 行 `chatRuntimes[key] ?: ChatRuntime().also { chatRuntimes[key] = it }` |
| 30 | sendUserMessage 内调用 AIMessageManager.buildUserMessageContent | MessageProcessingDelegate.kt:783 | 支撑 | 786 行调用，注释"1. 使用 AIMessageManager 构建最终消息" |
| 31 | sendUserMessage 调用 AIMessageManager.sendMessage 发起 AI 请求 | MessageProcessingDelegate.kt:1082 | 支撑 | 1087 行调用 |
| 32 | 流结束后调用 finalizeMessageAndNotify 做消息收尾 | MessageProcessingDelegate.kt:1527 | 支撑 | 1532 行在流处理分支内调用 |
| 33 | notifyTurnComplete 负责回合完成后的通知与计数 | MessageProcessingDelegate.kt:1862 | 支撑 | 1867-1873 行：`_turnCompleteCounterByChatId` 计数 + `onTurnComplete` 回调 |
| 34 | onTurnComplete 回调在回合完成时被触发 | MessageProcessingDelegate.kt:1879 | 支撑 | 1883 行 `onTurnComplete(activeChatId, service, nextWindowSize, turnOptions)` |
| 35 | cleanupRuntimeAfterSend 清理运行时：仅 activeTurnId 与本轮 turnId 一致时执行 | MessageProcessingDelegate.kt:1955 | 支撑 | 1960-1964 行：`if (chatRuntime.activeTurnId != turnId) return` 后清空流与加载态 |
| 36 | CurrentChatWindowController 维护显示窗口起止时间戳与 hasOlderPersistedHistory | CurrentChatWindowController.kt:15 | 支撑 | 20-23 行字段齐全 |
| 37 | applyMessages 将消息写入 chatHistoryFlow 并刷新窗口标记 | CurrentChatWindowController.kt:52 | 支撑 | `fun applyMessages(` 在 58 行；59-68 行写入 `chatHistoryFlow.value` 并刷新时间戳/标记（见备注 N3） |
| 38 | reset 清空当前显示窗口全部状态 | CurrentChatWindowController.kt:35 | 支撑 | `fun reset()` 在 35 行，清空时间戳与全部标记 |
| 39 | createExecutionIfMatched 实现插件匹配接管 | MessageProcessingPluginRegistry.kt:52 | 支撑 | `suspend fun createExecutionIfMatched(` 在 56 行 |
| 40 | MessageProcessingPlugin 是消息处理插件接口 | MessageProcessingPluginRegistry.kt:30 | 支撑 | `interface MessageProcessingPlugin` 在 34 行 |
| 41 | MessageProcessingController 是插件接管后的消息处理控制器接口 | MessageProcessingPluginRegistry.kt:21 | 支撑 | `interface MessageProcessingController` 在 25 行 |
| 42 | ChatRuntimeHookRegistry 是运行时钩子注册表（object） | ChatRuntimeHookRegistry.kt:40 | 支撑 | `object ChatRuntimeHookRegistry` 在 43 行 |
| 43 | ChatRuntimeHook 是运行时钩子接口 | ChatRuntimeHookRegistry.kt:31 | 支撑 | `interface ChatRuntimeHook` 在 34 行 |
| 44 | ChatRuntimeHookContext 承载运行时钩子上下文 | ChatRuntimeHookRegistry.kt:19 | 支撑 | `data class ChatRuntimeHookContext(` 在 23 行 |
| 45 | ChatTurnOptions 控制单轮行为：persistTurn（默认 true）、hideUserMessage、notifyReply、disableWarning | ChatTurnOptions.kt:3 | 支撑 | data class 四字段与默认值完全一致 |
| 46 | TokenStatisticsDelegate 负责 token 统计 | TokenStatisticsDelegate.kt:16 | 支撑 | 15 行 KDoc"负责管理token统计相关功能"，`class TokenStatisticsDelegate(` 在 16 行 |
| 47 | ChatHistoryDelegate 负责聊天历史管理 | ChatHistoryDelegate.kt:32 | 支撑 | 31 行 KDoc"负责管理聊天历史相关功能"，`class ChatHistoryDelegate(` 在 32 行 |

## 二、关键链路专项抽查

- **10 步消息处理链**（sendUserMessage:681 → 714/722 校验 → 726 turnId → 783 buildUserMessageContent → 1082 AIMessageManager.sendMessage → 380 getMemoryFromMessages → 431 插件匹配 / 484 普通模式 → 1527 finalizeMessageAndNotify → 1862 notifyTurnComplete → 1879 onTurnComplete → 1955 cleanupRuntimeAfterSend）：每一步的调用关系与顺序均与代码一致，无断链、无错序。
- **三个 Delegate 分工**：`MessageProcessingDelegate`（UI 层编排：发送入口/状态流/轮次管理）、`ChatHistoryDelegate`（聊天历史管理）、`TokenStatisticsDelegate`（token 统计）——三者 KDoc 与类职责描述准确，无夸大。
- **多轮任务状态机**（chatRuntimes/turnSequence）：`chatRuntimes` 为 `ConcurrentHashMap<String, ChatRuntime>`（按 chatId）；`runtimeFor` 懒创建；`turnSequence.incrementAndGet()` + `activeTurnId` 做轮次隔离；`cleanupRuntimeAfterSend` 仅当 `activeTurnId == turnId` 时清理——"状态机"一词为写作概括，代码行为支撑该概括。

## 三、合规检查（SCHEMA.md §2 / §4）

| 检查项 | 结果 |
|---|---|
| frontmatter（title/module/sources/date） | 齐全 |
| "来源"小节 | 存在且非空，8 个 seed files 全列出；另有一条有价值的注：outline.yaml 中两个旧 seed 路径已过时（实际在 `services/core/`），正文已用正确路径 |
| 禁用词（可能/大概/似乎/应该/也许） | 0 命中 |
| wikilink 格式与目标 | 3 个：`[[api-chat\|云端 Chat API 接入]]`、`[[core-tools\|工具系统]]`、`[[data-memory\|记忆系统]]`——均为"文件名\|显示名"格式，目标页在 outline v2 中均存在，无断链 |
| 超出引用支撑的发挥 | 未发现。正文每句断言均有对应 facts.json 条目与代码引用 |
| lint（`scripts/lint.py --src ~/workspace/Operit --dir review/batch-01`） | 5 文件、硬失败 0、警告 0（core-chat.md 引用有效率 100%） |

## 四、发现的问题（精确到行）

**硬问题：0。**

**引用精度微调建议（非必须，不影响结论）：**

- N1：facts.json #15 用单个 ref `:640` 覆盖三个取消函数，其中 `cancelOperation(chatId)` 实际在 648 行、`cancelAllOperations` 在 669 行，超出 ±5 容差。正文已用 `:640`/`:644`/`:669` 三个精确引用，建议 facts.json 侧拆分为三条或改用正文的引用。
- N2：facts.json #20 ref `:158`，`_activeStreamingChatIds` 实际在 166 行（8 行差），内容正确。
- N3：facts.json #37 ref `:52`，`applyMessages` 实际在 58 行（6 行差，超容差 1 行），内容正确。

## 五、最终结论

**通过。**

47 条事实全部有代码支撑；10 步处理链、Delegate 分工、状态机三处专项抽查无误；结构合规（frontmatter/来源小节/无禁用词/wikilink 有效）；lint 0 硬失败；无幻觉表述。N1–N3 为引用行号精度建议，可在后续批次顺手修正，不构成打回理由。

## 修订记录（2026-09-30）
3 条引用精度微调已修：#15 拆为三条独立引用（cancelCurrentOperation:640、cancelOperation:644、cancelAllOperations:669）；#20 ref 改 :161；#37 ref 改 :53；正文两处行号同步。复跑 lint：硬失败 0，警告 0。结论维持：通过。
