---
title: 云端 Chat API 接入
module: app
sources: 18
date: 2026-09-30
---

# 云端 Chat API 接入

## 概述

`api/chat` 是 Operit 对接云端与本地大模型的统一接入层：上层只依赖 `AIService` 接口，`AIServiceFactory` 按渠道类型装配具体实现，为 [[core-chat|聊天与消息处理]] <!-- confidence: INFERRED --> 提供模型调用能力。

## 关键符号

- `AIService`：全部模型渠道统一实现的接口 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:12`
- `providerModel` 返回"供应商:模型"标识，格式如 `DEEPSEEK:deepseek-chat` `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:23`
- `sendMessage`：收 `chatHistory`、`modelParameters`、`enableThinking`、`stream`，统一返回 `Stream<String>` `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:60`
- `getModelsList` 拉取渠道的可用模型列表 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:37`
- `testConnection` 测试与渠道的连接 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:82`
- `calculateInputTokens` 精确计算下一次请求的输入 token 数 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:91`
- `cancelStreaming` 取消当前流式传输 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:29`
- `inputTokenCount`、`cachedInputTokenCount` 输入 token 计数器 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:14`
- `outputTokenCount` 输出 token 计数器 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:20`
- `release` 默认空实现，本地模型（如 MNN）覆盖它以释放 native 资源 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:101`
- `ApiProviderType` 枚举定义 OpenAI 系渠道：`OPENAI`、`XAI`、`OPENAI_RESPONSES`、`OPENAI_CODEX`、`OPENAI_RESPONSES_GENERIC`、`OPENAI_GENERIC` `app/src/main/java/com/ai/assistance/operit/data/model/ModelConfigData.kt:9`
- `ANTHROPIC`、`GOOGLE`（Gemini）及各自 `ANTHROPIC_GENERIC`、`GEMINI_GENERIC` 自定义端点类型 `app/src/main/java/com/ai/assistance/operit/data/model/ModelConfigData.kt:15`
- 国产云端渠道：`BAIDU`、`ALIYUN`（通义千问）、`XUNFEI`、`ZHIPU`、`BAICHUAN`、`MOONSHOT`、`MIMO`、`DEEPSEEK` `app/src/main/java/com/ai/assistance/operit/data/model/ModelConfigData.kt:21`
- 聚合与第三方渠道：`MISTRAL`、`SILICONFLOW`、`IFLOW`、`OPENROUTER`、`OPENCODE`、`FOUR_ROUTER`、`NOUS_PORTAL`、`INFINIAI`、`ALIPAY_BAILING`、`DOUBAO`、`NVIDIA` `app/src/main/java/com/ai/assistance/operit/data/model/ModelConfigData.kt:31`
- 本地/端侧渠道：`LMSTUDIO`、`OLLAMA`、`OPENAI_LOCAL`、`MNN`、`LLAMA_CPP` `app/src/main/java/com/ai/assistance/operit/data/model/ModelConfigData.kt:39`
- 其他云端渠道：`PPINFRA`、`NOVITA`、`MINIMAX`，`OTHER` 兜底自定义端点 `app/src/main/java/com/ai/assistance/operit/data/model/ModelConfigData.kt:43`
- 统一建服务入口：返回前用 `TokenTrackingAIService` 包裹原始服务 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:275`
- 渠道装配先查 `ToolPkgAiProviderRegistry`，命中则走 `ToolPkgJsAiProviderService`（工具包 JS 渠道） `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:287`
- 未命中 JS 注册表时按 `ApiProviderType` 映射实现类，未知 id 抛 `IllegalArgumentException` `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:297`
- `SharedHttpClient` 全局共享 OkHttp：连接超时 60 秒，读/写超时 1000 秒 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:202`
- 连接池 10 个空闲连接、5 分钟保活，协议 `HTTP_2` 优先、回退 `HTTP_1_1` `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:209`
- `SingleApiKeyProvider` 单 Key 实现 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/ApiKeyProvider.kt:24`
- `MultiApiKeyProvider` 多 Key 轮询实现 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/ApiKeyProvider.kt:38`
- 配置开 `useMultipleApiKeys` 时选用 `MultiApiKeyProvider` 做多 Key 轮询 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:303`
- `TokenTrackingAIService`：只在拿到渠道真实 usage 时才写入 token 统计账本 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/TokenTrackingAIService.kt:28`
- `RateLimitedAIService` 包装 `AIService`，接入 `SlidingWindowRateLimiter` 做限流 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/RateLimitedAIService.kt:14`
- `LlmRetryPolicy.MAX_RETRY_ATTEMPTS` 为 5 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/LlmRetryPolicy.kt:4`
- `DeepseekProvider`：DeepSeek 渠道实现类 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/DeepseekProvider.kt:25`
- `ModelListFetcher` 从不同渠道获取可用模型列表 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/ModelListFetcher.kt:27`
- `EndpointCompleter` 自动补全 API 端点 URL `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/EndpointCompleter.kt:9`
- `EnhancedAIService`：api/chat 的统一门面（单例） `app/src/main/java/com/ai/assistance/operit/api/chat/EnhancedAIService.kt:97`
- `EnhancedAIService.sendMessage` 收 `SendMessageOptions`（含 `chatHistory` 与各类回调） `app/src/main/java/com/ai/assistance/operit/api/chat/EnhancedAIService.kt:903`
- `MultiServiceManager`：多渠道实例管理器 `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/MultiServiceManager.kt:23`
- `getServiceForFunction` 按 `FunctionType` 取对应渠道服务 `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/MultiServiceManager.kt:81`
- `acquireServiceForFunction` 返回 `ServiceLease` `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/MultiServiceManager.kt:96`
- `ServiceLease` 携带 `service`、`modelConfig`、`modelParameters` `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/MultiServiceManager.kt:28`
- `FunctionType` 枚举 11 种功能：`CHAT`、`SUMMARY`、`TITLE_GENERATION`、`MEMORY`、`UI_CONTROLLER`、`TRANSLATION`、`GREP`、`ROLE_RESPONSE_PLANNER`、`IMAGE_RECOGNITION` `app/src/main/java/com/ai/assistance/operit/data/model/FunctionType.kt:8`
- 另有 `AUDIO_RECOGNITION`、`VIDEO_RECOGNITION` 音视频识别功能 `app/src/main/java/com/ai/assistance/operit/data/model/FunctionType.kt:14`
- `ConversationService.processChatMessageWithTools`：带工具调用的聊天主流程 `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ConversationService.kt:718`
- `ConversationService.prepareConversationHistory` 组装发往模型的对话历史 `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ConversationService.kt:447`
- `ToolExecutionManager.extractToolInvocations` 从模型响应中提取工具调用 `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt:306`
- `AIForegroundService`：前台保活服务，在 AI 长时间处理时保持进程活跃，自身不执行业务 `app/src/main/java/com/ai/assistance/operit/api/chat/AIForegroundService.kt:101`
- `ChatRuntimeHolder.getCore` 按 `ChatRuntimeSlot` 取聊天运行时 `app/src/main/java/com/ai/assistance/operit/api/chat/ChatRuntimeHolder.kt:40`

## 新增一个渠道

1. 在 `ApiProviderType` 枚举加一个值 `app/src/main/java/com/ai/assistance/operit/data/model/ModelConfigData.kt:7`
2. 新建渠道实现类，实现 `AIService` 接口 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIService.kt:12`
3. 在 `providerType` 的 when 映射里加分支 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:316`
4. 未知 id 会抛 `IllegalArgumentException` `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:297`
5. 不改原生代码的另一条路：向 `ToolPkgAiProviderRegistry` 注册工具包 JS 渠道，装配时会优先命中它 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:287`

## 请求构造与流式响应链路

1. 上层调用 `EnhancedAIService.sendMessage`，传入 `SendMessageOptions`（含 `chatHistory`、回调） `app/src/main/java/com/ai/assistance/operit/api/chat/EnhancedAIService.kt:903`
2. `MultiServiceManager.getServiceForFunction` 按 `FunctionType`（对话/总结/翻译/识图等 11 种）取出对应渠道的 `AIService` `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/MultiServiceManager.kt:81`
3. `AIServiceFactory.createService` 装配实例并用 `TokenTrackingAIService` 包裹做统计记账 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:275`
4. Provider 的 `createRequestBody` 把聊天历史、模型参数、工具列表拼成 JSON 请求体 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/OpenAIProvider.kt:577`
5. `createRequest` 组装 OkHttp 请求：端点经 `EndpointCompleter.completeEndpoint` 补全 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/OpenAIProvider.kt:1818`
6. 请求头含 `Content-Type: application/json` 与自定义 `customHeaders` `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/OpenAIProvider.kt:1836`
7. `applyAuthenticationHeaders` 添加 `Authorization: Bearer` 认证头 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/OpenAIProvider.kt:240`
8. 请求经 `SharedHttpClient` 发出 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/AIServiceFactory.kt:294`
9. 按 `LlmRetryPolicy.MAX_RETRY_ATTEMPTS`（5 次）重试，失败回滚到请求起点重发 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/OpenAIProvider.kt:3238`
10. 流式响应逐行解析 SSE：`data:` 行解析为事件，`[DONE]` 表示流结束 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/OpenAIProvider.kt:3122`
11. 思考内容经 `emitThinkContent` 先发射，常规内容随后发射 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/OpenAIProvider.kt:3091`
12. 收到 `[DONE]` 后收拢未闭合的工具调用并闭合 think 标签 `app/src/main/java/com/ai/assistance/operit/api/chat/llmprovider/OpenAIProvider.kt:3129`
13. 带工具调用时走 `ConversationService.processChatMessageWithTools` 循环：发消息 → `ToolExecutionManager.extractToolInvocations` 提取调用 → 执行 → 结果回填再发 `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ConversationService.kt:718`

## 内部分层

seed 目录实际扫描 61 个 kt 文件，分四部分：

- 顶层（4 文件）：`EnhancedAIService` 统一门面、`AIForegroundService` 前台保活、`ChatRuntimeHolder`/`ChatRuntimeSlot` 运行时槽位
- `llmprovider/`（43 文件）：`AIService` 接口、`AIServiceFactory` 装配、20 个 `XxxProvider` 渠道实现，以及限流（`RateLimitedAIService`）、重试（`LlmRetryPolicy`）、统计（`TokenTrackingAIService`）装饰器与辅助工具（`ModelListFetcher`、`EndpointCompleter`、`MediaLinkBuilder` 等）
- `enhance/`（9 文件）：`ConversationService` 会话编排、`ToolExecutionManager` 工具执行、`MultiServiceManager` 多服务管理、`InputProcessor` 输入处理等上层逻辑
- `library/`（5 文件）：记忆库相关（`MemoryLibrary`、`ChatMemoryRebuildManager` 等），详见 [[data-memory|记忆系统]]

## 来源

- seed 目录：`app/src/main/java/com/ai/assistance/operit/api/chat/`（顶层 4 文件、`enhance/` 9 文件、`library/` 5 文件、`llmprovider/` 43 文件）
- 关联引用：`app/src/main/java/com/ai/assistance/operit/data/model/ModelConfigData.kt`（`ApiProviderType` 渠道枚举）、`app/src/main/java/com/ai/assistance/operit/data/model/FunctionType.kt`（功能类型枚举）
