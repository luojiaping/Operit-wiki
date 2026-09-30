---
title: 聊天与消息处理
module: app
sources: [app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt, app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt, app/src/main/java/com/ai/assistance/operit/services/core/CurrentChatWindowController.kt, app/src/main/java/com/ai/assistance/operit/core/chat/plugins/MessageProcessingPluginRegistry.kt, app/src/main/java/com/ai/assistance/operit/core/chat/hooks/ChatRuntimeHookRegistry.kt, app/src/main/java/com/ai/assistance/operit/data/model/ChatTurnOptions.kt, app/src/main/java/com/ai/assistance/operit/services/core/TokenStatisticsDelegate.kt, app/src/main/java/com/ai/assistance/operit/services/core/ChatHistoryDelegate.kt]
date: 2026-09-30
---

# 聊天与消息处理

## 概述

聊天与消息处理是 Operit 的核心链路：用户输入从 `MessageProcessingDelegate.sendUserMessage` 进入（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:681`）。
请求内容由 `AIMessageManager.buildUserMessageContent` 组装（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:126`）。
组装后的请求经 `AIMessageManager.sendMessage` 转交 `EnhancedAIService` 发起调用（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:346`），`EnhancedAIService` 的实现见 [[api-chat|云端 Chat API 接入]]。

## 关键符号

### AIMessageManager（`core/chat`）

该单例负责管理与 `EnhancedAIService` 的所有通信（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:67`）。
`AIMessageManager`（`object`）设计无状态：不持有特定聊天状态，所有数据经方法参数传入（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:80`）。
`initialize` 初始化 `toolHandler`（`AIToolHandler.getInstance`）、`packageManager`、`apiPreferences`（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:105`），其中工具相关能力由 [[core-tools|工具系统]] 提供。
`sendMessage` 是消息发送主入口（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:346`）。
先调用 `getMemoryFromMessages` 把聊天历史转成可发送的记忆（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:380`），记忆体系见 [[data-memory|记忆系统]]。
聊天历史中的图片链接会被数量裁剪，由 `limitImageLinksInChatHistory` 执行（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:612`）。
聊天历史中的音视频链接会被数量裁剪，由 `limitMediaLinksInChatHistory` 执行（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:588`）。
先尝试 `MessageProcessingPluginRegistry.createExecutionIfMatched`；插件匹配则由插件接管处理，否则走普通模式（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:431`）。
普通模式调用 `enhancedAiService.sendMessage` 构造 `SendMessageOptions` 发起请求（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:484`）。
`buildUserMessageContent` 负责组装用户消息的最终内容（含附件与记忆标签）（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:126`）。
消息构建时先经 `InputProcessor.processUserInput` 处理用户原始输入（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:144`）。
`<proxy_sender>` 标签携带代发人名称（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:161`）。
`<reply_to>` 标签携带被回复消息的发送者、时间戳与内容（超 100 字符截断）（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:176`）。
`<workspace_attachment>` 标签封装工作区变更，由 `WorkspaceChangeTracker.consumeChanges` 获取、`WorkspaceAttachmentProcessor.generateWorkspaceAttachment` 生成（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:194`）。
各阶段耗时经 `logMessageTiming` 记录，日志 tag 为 `MESSAGE_PROCESS_TIMING_TAG`（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:49`）。
`cancelCurrentOperation` 取消当前操作（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:640`）。
`cancelOperation(chatId)` 按会话取消（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:644`）。
`cancelAllOperations` 取消全部操作（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:669`）。
`summarizeMemory` 负责生成记忆总结（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:684`）。
`shouldGenerateSummary` 判断是否需要生成对话总结（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:1281`）。

### MessageProcessingDelegate（`services/core`）

`MessageProcessingDelegate` 是面向 UI 的消息处理编排类，构造函数注入 `getEnhancedAiService` 等回调（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:54`）。
输入草稿由 `_userMessage`（`MutableStateFlow`）持有，对外暴露为 `userMessage`（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:152`）。
`_isLoading` 与 `_activeStreamingChatIds` 分别暴露加载态与正在流式输出的会话集合（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:161`）。
`_inputProcessingStateByChatId` 按 chatId 记录输入处理状态（`EnhancedInputProcessingState`）（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:164`）。
流式输出节流：`STREAM_SCROLL_THROTTLE_MS` 为 200ms，`STREAM_PERSIST_INTERVAL_MS` 为 1000ms（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:80`）。
`sendUserMessage` 是用户消息发送入口（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:681`）。
空消息且无附件（且非自动续写/群组编排）时 `sendUserMessage` 直接忽略（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:714`）。
同会话正在处理中（`chatRuntime.isLoading`）时新的发送请求被忽略（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:722`）。

### Delegate 分工

`MessageProcessingDelegate` 负责 UI 层编排：发送入口、状态流与轮次管理（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:54`）。
`ChatHistoryDelegate` 负责聊天历史管理（`app/src/main/java/com/ai/assistance/operit/services/core/ChatHistoryDelegate.kt:32`）。
`TokenStatisticsDelegate` 负责 token 统计（`app/src/main/java/com/ai/assistance/operit/services/core/TokenStatisticsDelegate.kt:16`）。

### 运行时状态与显示窗口

`ChatRuntime` 是按 chatId 维护的运行时状态：`sendJob`、`responseStream`、`activeStreamingTurn`（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:203`）。
各会话的 `ChatRuntime` 存放在 `chatRuntimes`（`ConcurrentHashMap`）（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:224`）。
`runtimeFor(chatId)` 懒创建并返回对应会话的 `ChatRuntime`（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:244`）。
轮次隔离：每轮分配 `turnId = chatRuntime.turnSequence.incrementAndGet()` 并设为 `activeTurnId`（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:726`）。
`cleanupRuntimeAfterSend` 在发送后清理运行时：仅当 `activeTurnId` 与本轮 `turnId` 一致时执行，清空流与加载态（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:1955`）。
`CurrentChatWindowController` 维护当前显示窗口的起止时间戳（`displayStartTimestamp`/`displayEndTimestamp`）与是否有更早持久化历史的标记（`hasOlderPersistedHistory`）（`app/src/main/java/com/ai/assistance/operit/services/core/CurrentChatWindowController.kt:15`）。
`applyMessages` 将加载到的消息写入 `chatHistoryFlow` 并刷新窗口标记（`app/src/main/java/com/ai/assistance/operit/services/core/CurrentChatWindowController.kt:53`）。
`reset` 清空当前显示窗口的全部状态（`app/src/main/java/com/ai/assistance/operit/services/core/CurrentChatWindowController.kt:35`）。

### 插件、钩子与单轮选项

`createExecutionIfMatched` 实现插件匹配接管（`app/src/main/java/com/ai/assistance/operit/core/chat/plugins/MessageProcessingPluginRegistry.kt:52`）。
`MessageProcessingPlugin` 是消息处理插件接口（`app/src/main/java/com/ai/assistance/operit/core/chat/plugins/MessageProcessingPluginRegistry.kt:30`）。
`MessageProcessingController` 是插件接管后的消息处理控制器接口（`app/src/main/java/com/ai/assistance/operit/core/chat/plugins/MessageProcessingPluginRegistry.kt:21`）。
`ChatRuntimeHookRegistry` 是运行时钩子注册表（`object`）（`app/src/main/java/com/ai/assistance/operit/core/chat/hooks/ChatRuntimeHookRegistry.kt:40`）。
`ChatRuntimeHook` 是运行时钩子接口（`app/src/main/java/com/ai/assistance/operit/core/chat/hooks/ChatRuntimeHookRegistry.kt:31`）。
`ChatRuntimeHookContext` 承载运行时钩子的上下文（`app/src/main/java/com/ai/assistance/operit/core/chat/hooks/ChatRuntimeHookRegistry.kt:19`）。
`ChatTurnOptions` 控制单轮行为：`persistTurn`（默认 true，是否落库）、`hideUserMessage`、`notifyReply`、`disableWarning`（`app/src/main/java/com/ai/assistance/operit/data/model/ChatTurnOptions.kt:3`）。

## 流程/数据流

一条用户消息从进入到回复的完整处理链：

1. UI 调用 `MessageProcessingDelegate.sendUserMessage`（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:681`）。
2. 校验：空消息且无附件时直接忽略（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:714`）；同会话正在处理中时忽略新请求（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:722`）。
3. 分配本轮 `turnId` 并设为 `activeTurnId`，实现轮次隔离（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:726`）。
4. 调用 `AIMessageManager.buildUserMessageContent` 构建最终消息内容（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:783`）。
5. 调用 `AIMessageManager.sendMessage` 发起 AI 请求（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:1082`）。
6. 先把聊天历史转成可发送的记忆（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:380`）。
   插件匹配时由插件接管处理（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:431`），否则调用 `enhancedAiService.sendMessage`（`app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt:484`）。
7. 流结束后调用 `finalizeMessageAndNotify` 做消息收尾（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:1527`）。
8. `notifyTurnComplete` 做回合完成通知与计数（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:1862`）。
9. `onTurnComplete` 回调在回合完成时被触发（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:1879`）。
10. `cleanupRuntimeAfterSend` 清理本轮运行时状态（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:1955`）。

多轮任务的状态机按 chatId 维护在 `chatRuntimes` 中（`ChatRuntime` 实例）（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:224`）。
`turnSequence`/`activeTurnId` 做轮次隔离（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:726`）。
`runtimeFor` 懒创建对应会话的运行时（`app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt:244`）。

## 来源

- `app/src/main/java/com/ai/assistance/operit/core/chat/AIMessageManager.kt`
- `app/src/main/java/com/ai/assistance/operit/services/core/MessageProcessingDelegate.kt`
- `app/src/main/java/com/ai/assistance/operit/services/core/CurrentChatWindowController.kt`
- `app/src/main/java/com/ai/assistance/operit/core/chat/plugins/MessageProcessingPluginRegistry.kt`
- `app/src/main/java/com/ai/assistance/operit/core/chat/hooks/ChatRuntimeHookRegistry.kt`
- `app/src/main/java/com/ai/assistance/operit/data/model/ChatTurnOptions.kt`
- `app/src/main/java/com/ai/assistance/operit/services/core/TokenStatisticsDelegate.kt`
- `app/src/main/java/com/ai/assistance/operit/services/core/ChatHistoryDelegate.kt`

注：outline.yaml 中 `core/MessageProcessingDelegate.kt` 与 `core/CurrentChatWindowController.kt` 两个 seed 路径已过时，实际位于 `services/core/`。
