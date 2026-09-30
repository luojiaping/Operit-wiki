# Critic 评审报告：api-chat（云端 Chat API 接入）

- 评审对象：`review/batch-01/api-chat.md`（94 行）
- 事实源：`wiki-work/facts/batch-01/api-chat.facts.json`（48 条）
- 评审依据：SCHEMA.md（引用铁律 / 禁用词 / 评审标准四项）
- 评审方式：独立 session，逐条打开 ref 代码行 ±5 行窗口核对；另抽查正文超出 facts 的断言
- 评审日期：2026-09-30

## 一、逐条事实判定表

| # | 事实摘要 | ref | 判定 | 备注 |
|---|---------|-----|------|------|
| F0 | AIService 是渠道统一接口 | AIService.kt:12 | 支撑 | `interface AIService`，doc 一致 |
| F1 | providerModel 返回"供应商:模型" | AIService.kt:23 | 支撑 | doc 明确格式如 `DEEPSEEK:deepseek-chat` |
| F2 | sendMessage 参数与返回 Stream | AIService.kt:60 | 支撑 | chatHistory/modelParameters/enableThinking/stream 均在签名；KDoc 注明总返回 Stream |
| F3 | getModelsList | AIService.kt:37 | 支撑 | 签名一致 |
| F4 | testConnection | AIService.kt:82 | 支撑 | doc"测试与AI服务的连接" |
| F5 | calculateInputTokens | AIService.kt:91 | 支撑 | doc"精确计算下一次请求的输入Token数量" |
| F6 | cancelStreaming | AIService.kt:29 | 支撑 | |
| F7 | 三组 token 计数器 | AIService.kt:14 | 支撑 | inputTokenCount(:14)/cachedInputTokenCount(:17)/outputTokenCount(:20) 均在 ±5 行内 |
| F8 | release 默认空实现，MNN 覆盖释 native 资源 | AIService.kt:101 | 支撑 | doc 原文一致 |
| F9 | OpenAI 系渠道（OPENAI/XAI/OPENAI_RESPONSES/OPENAI_CODEX 等） | ModelConfigData.kt:9 | 支撑 | 有"等"字；枚举 :8-13 含 OPENAI_RESPONSES_GENERIC、OPENAI_GENERIC |
| F10 | ANTHROPIC/ANTHROPIC_GENERIC/GOOGLE/GEMINI_GENERIC | ModelConfigData.kt:15 | 支撑 | :14-17 四值齐全 |
| F11 | 国产 8 渠道 | ModelConfigData.kt:21 | 支撑 | :18-25 八值齐全 |
| F12 | 聚合/第三方渠道…等 | ModelConfigData.kt:30 | 支撑 | 有"等"字 |
| F13 | 本地/端侧渠道 + OTHER | ModelConfigData.kt:38 | 支撑 | :37-45 含 LMSTUDIO/OLLAMA/OPENAI_LOCAL/MNN/LLAMA_CPP/OTHER |
| F14 | createService 统一入口，TokenTrackingAIService 包裹 | AIServiceFactory.kt:275 | 支撑 | :274-279 装配链一致 |
| F15 | buildService 先查 ToolPkgAiProviderRegistry | AIServiceFactory.kt:287 | 支撑 | :287-292 命中即返回 ToolPkgJsAiProviderService |
| F16 | when 穷举 ApiProviderType 映射实现类 | AIServiceFactory.kt:281 | 支撑 | :316 起 `return when (providerType)`，多分支已实测 |
| F17 | 未知 id 抛 IllegalArgumentException | AIServiceFactory.kt:297 | 支撑 | :296-300 原文一致 |
| F18 | useMultipleApiKeys 切多 Key 轮询 | AIServiceFactory.kt:303 | 支撑 | :303-307 |
| F19 | SharedHttpClient 超时 60s 连接 / 1000s 读写 | AIServiceFactory.kt:202 | 支撑 | :202-205 |
| F20 | 连接池 10 空闲/5 分钟保活，HTTP_2 优先 | AIServiceFactory.kt:209 | 支撑 | :209-212 |
| F21 | createRequest 用 EndpointCompleter 补全端点 | OpenAIProvider.kt:1818 | 支撑 | :1823 `EndpointCompleter.completeEndpoint(apiEndpoint, providerType)` |
| F22 | applyAuthenticationHeaders 加 Bearer 头 | OpenAIProvider.kt:240 | 支撑 | :240 原文 |
| F23 | Content-Type + customHeaders | OpenAIProvider.kt:1836 | 支撑 | :1836-1842 |
| F24 | POST 发出请求体 | OpenAIProvider.kt:1845 | 支撑 | :1845 `builder.post(requestBody)` |
| F25 | 按 MAX_RETRY_ATTEMPTS 重试，失败回滚到请求起点 | OpenAIProvider.kt:3238 | 支撑 | :3238 取值；:3242 注释"整体回滚到请求起点" |
| F26 | MAX_RETRY_ATTEMPTS = 5 | LlmRetryPolicy.kt:4 | 支撑 | |
| F27 | SSE 逐行解析，`[DONE]` 结束 | OpenAIProvider.kt:3122 | 支撑 | :3122-3127 |
| F28 | reasoningContent 先发射 think 内容 | OpenAIProvider.kt:3090 | 支撑 | :3090-3091 `emitThinkContent` |
| F29 | `[DONE]` 后收拢工具调用、闭合 think 标签 | OpenAIProvider.kt:3129 | 支撑 | :3129-3133 |
| F30 | TokenTrackingAIService 只在真实 usage 时记账 | TokenTrackingAIService.kt:28 | 支撑 | KDoc "provider-confirmed usage" |
| F31 | RateLimitedAIService + SlidingWindowRateLimiter | RateLimitedAIService.kt:14 | 支撑 | :14-18 |
| F32 | DeepseekProvider.create 构造入口 | DeepseekProvider.kt:55 | 支撑 | companion `fun create(` |
| F33 | EnhancedAIService 单例统一门面 | EnhancedAIService.kt:97 | 支撑 | `private constructor` |
| F34 | getInstance 取单例 | EnhancedAIService.kt:118 | 支撑 | 双重检查锁 |
| F35 | sendMessage 收 SendMessageOptions，总入口 | EnhancedAIService.kt:903 | 支撑 | :903-908 |
| F36 | MultiServiceManager 按 FunctionType 分发多实例 | MultiServiceManager.kt:23 | 支撑 | doc 一致 |
| F37 | getServiceForFunction | MultiServiceManager.kt:81 | 支撑 | |
| F38 | acquireServiceForFunction 返回 ServiceLease | MultiServiceManager.kt:96 | 支撑 | :96；ServiceLease(:28-32) 含 service/modelConfig/modelParameters，`close()` 可关 |
| F39 | FunctionType 11 种之前 9 种 | FunctionType.kt:8 | 支撑 | :5-13 |
| F40 | AUDIO/VIDEO_RECOGNITION | FunctionType.kt:14 | 支撑 | :14-15；合计 11 种 ✓ |
| F41 | processChatMessageWithTools 主流程 | ConversationService.kt:718 | 支撑 | doc"处理包含工具结果的聊天消息" |
| F42 | prepareConversationHistory 组装历史 | ConversationService.kt:447 | 支撑 | doc"准备好的对话历史列表" |
| F43 | extractToolInvocations 提取工具调用 | ToolExecutionManager.kt:306 | 支撑 | doc 一致 |
| F44 | AIForegroundService 保活、自身不执行业务 | AIForegroundService.kt:101 | 支撑 | :100 doc 原文 |
| F45 | ChatRuntimeHolder.getCore 按槽位取运行时 | ChatRuntimeHolder.kt:40 | 支撑 | |
| F46 | ModelListFetcher 拉取模型列表 | ModelListFetcher.kt:27 | 支撑 | doc"从不同API提供商获取可用模型列表" |
| F47 | EndpointCompleter 补全端点 URL | EndpointCompleter.kt:9 | 支撑 | doc 一致 |

**事实判定汇总：48 条全部"支撑"，0 不支撑，0 存疑。**

## 二、正文检查

- **禁用词**：`可能/大概/似乎/应该/也许` 全文 0 命中 ✓
- **frontmatter**：title / module / sources / date 齐全；`sources: 18` 与正文实际引用的 18 个源文件数一致 ✓
- **"来源"小节**：存在且非空 ✓
- **wikilink**：`[[core-chat|聊天与消息处理]]`、`[[data-memory|记忆系统]]` 目标 id 在 outline.yaml（v2）中均存在；前者已标 `confidence: INFERRED` ✓
- **引用符号 ±5 行规则**：抽查 48 条全部命中 ✓
- **正文超出 facts 的断言**（内部分层、链路步骤）：逐项实测——
  - 顶层 4 / llmprovider 43 / enhance 9 / library 5 文件，共 61 ✓
  - `*Provider.kt` 21 个文件，减去 `ApiKeyProvider.kt`（Key 管理非渠道实现）= 20 个渠道实现 ✓
  - `MediaLinkBuilder.kt`、`InputProcessor.kt` 存在 ✓
  - 链路 13 步每步引用均有效（`createRequestBody` 在 OpenAIProvider.kt:577 实测存在，参数含 chatHistory/modelParameters/availableTools ✓）

## 三、发现的问题（精确到行）

### P1（需修改）：渠道分组枚举不完整，读作穷举（md 行 21–25）

`ApiProviderType` 枚举实测共 **38** 值（`OTHER;` 以分号结尾，37 个逗号项 +1）。正文五个分组只列出 30 个，遗漏 8 个且未写"等"：

- 行 21"OpenAI 系"漏 `OPENAI_RESPONSES_GENERIC`、`OPENAI_GENERIC`（ModelConfigData.kt:12–13）
- 行 24"聚合与第三方"漏 `IFLOW`、

...[truncated 1155 chars]
## 修订记录（2026-09-30）
2 项问题已修：P1 渠道分组补全为 38 值全名单（补 OPENAI_RESPONSES_GENERIC、OPENAI_GENERIC、IFLOW、INFINIAI、ALIPAY_BAILING、PPINFRA、NOVITA、MINIMAX；本地/端侧组拆出"其他云端渠道"行，各行引用窗口已对齐）；P2 步骤 3 拆为两条（when 映射 :316、未知 id 抛异常 :297）。复跑 lint：硬失败 0，警告 0。结论更新为：通过。
