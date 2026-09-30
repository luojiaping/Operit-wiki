---
title: 工具系统
module: app
sources: 15
date: 2026-09-30
---

# 工具系统

## 概述

工具系统是 Operit Agent 调用外部能力的统一入口：模型输出中的工具调用被解析出来，经过拦截与权限检查后执行，结果回填进对话，驱动多轮任务。注册、发现、执行全部收敛在 `AIToolHandler` 单例。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:29`

## 关键符号

- `AITool`：工具的数据模型，字段为 `name`、`parameters`、`description`。`app/src/main/java/com/ai/assistance/operit/data/model/AITool.kt:12`
- `ToolParameter`：参数模型，字段为 `name`、`value`，均为字符串。`app/src/main/java/com/ai/assistance/operit/data/model/AITool.kt:8`
- `ToolResult`：执行结果，字段为 `toolName`、`success`、`result`、`error`。`app/src/main/java/com/ai/assistance/operit/data/model/AITool.kt:29`
- `ToolInvocation`：模型响应中的一次工具调用，字段为 `tool`、`rawText`、`responseLocation`。`app/src/main/java/com/ai/assistance/operit/data/model/AITool.kt:20`
- `availableTools`：`ConcurrentHashMap` 注册表，键为工具名，值为 `ToolExecutor`。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:45`
- `registerTool`：向注册表登记工具的方法，接受名称、可选的描述生成器与执行器。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:179`
- `registerDefaultTools`：幂等注册全部内置工具，双重检查保证只执行一次。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:211`
- `registerAllTools`：在 `ToolRegistration.kt` 中集中完成全部内置工具的注册。`app/src/main/java/com/ai/assistance/operit/core/tools/ToolRegistration.kt:36`
- `getAllToolNames`：返回已注册工具名的排序列表。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:160`
- `ToolExecutor`：执行器接口，`invoke` 必须实现，`invokeAndStream` 有默认实现，参数校验默认返回有效。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:479`
- `executeToolAndStream`：返回 `Flow<ToolResult>` 的流式执行入口，保留中间结果。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:419`
- `AIToolHook`：工具调用生命周期钩子，`onToolCallIntercept` 决定本次调用是否放行。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHook.kt:21`
- 另有 `onToolPermissionChecked`、`onToolExecutionError` 等回调。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHook.kt:28`
- `extractToolInvocations`：从流式响应文本中解析出 `ToolInvocation` 列表。`app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt:306`
- `executeInvocations`：批量执行入口，先确保默认工具已注册，再做暴露模式与角色卡权限拦截。`app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt:504`
- `executeTool`：同步执行入口，顺序为拦截检查、获取执行器、校验参数、执行。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:363`
- `getToolExecutorOrActivate`：按名取执行器；缺失时先补注册，`packName:toolName` 形式自动激活对应工具包。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:303`
- `replaceToolInvocation`：把响应中的调用原文替换为工具结果块回填。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:233`
- `aggregateToolResults`：把一次调用的多个流式结果拼接，成功态取最后一次。`app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt:710`
- `toToolPackage`：把 MCP 工具定义转换为标准 `ToolPackage`，分类记为 MCP。`app/src/main/java/com/ai/assistance/operit/core/tools/mcp/MCPPackage.kt:133`
- `MCPTool`：MCP 工具定义，字段为 `name`、`description`、`parameters`。`app/src/main/java/com/ai/assistance/operit/core/tools/mcp/MCPTool.kt:9`
- `MCPToolExecutor`：实现 `ToolExecutor` 的 MCP 调用执行器。`app/src/main/java/com/ai/assistance/operit/core/tools/mcp/MCPToolExecutor.kt:23`
- `PackageManager`：ToolPkg 包的管理类。`app/src/main/java/com/ai/assistance/operit/core/tools/packTool/PackageManager.kt:62`
- `usePackage`：按包名激活一个工具包。`app/src/main/java/com/ai/assistance/operit/core/tools/packTool/PackageManager.kt:3246`
- `SkillManager`：技能包管理的单例。`app/src/main/java/com/ai/assistance/operit/core/tools/skill/SkillManager.kt:12`
- `JsEngine`：JavaScript 脚本引擎。`app/src/main/java/com/ai/assistance/operit/core/tools/javascript/JsEngine.kt:49`
- `StandardShellToolExecutor`：内置标准工具集中的 shell 执行器。`app/src/main/java/com/ai/assistance/operit/core/tools/defaultTool/standard/StandardShellToolExecutor.kt:18`
- `AndroidShellExecutor`：system 层提供的系统级 shell 执行能力。`app/src/main/java/com/ai/assistance/operit/core/tools/system/AndroidShellExecutor.kt:11`
- `PhoneAgent`：agent 目录下的专用工具。`app/src/main/java/com/ai/assistance/operit/core/tools/agent/PhoneAgent.kt:119`

## 流程：模型输出 → 解析 → 执行 → 结果回填

1. 模型流式输出文本，`extractToolInvocations` 逐块扫描，产出 `ToolInvocation` 列表。`app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt:306`
2. 解析用 `toolCallPattern` 匹配调用标签，用 `toolParamPattern` 解析参数。`app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt:321`
3. `executeInvocations` 先确保默认工具已注册，再依次做工具暴露模式拦截与角色卡工具权限拦截。`app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt:504`
4. `executeTool` 是同步执行入口：先过 `AIToolHook` 拦截检查，再获取执行器、校验参数并执行。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:363`
5. 找不到执行器时先补一次默认注册；工具名形如 packName:toolName 时自动激活对应工具包。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:303`
6. `aggregateToolResults` 把流式执行的多个 `ToolResult` 拼接为单个结果。`app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt:710`
7. `replaceToolInvocation` 把响应原文中的调用替换为结果块，完成回填。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:233`

## ToolPkg 格式与 MCP 的关系

- `.toolpkg` 文件本质上是一个标准的 ZIP 压缩包。`docs/TOOLPKG_FORMAT_GUIDE.md:11`
- `manifest.json` 为必需的清单文件。`docs/TOOLPKG_FORMAT_GUIDE.md:34`
- `main.js` 为必需的主入口脚本。`docs/TOOLPKG_FORMAT_GUIDE.md:35`
- manifest 字段包括 `schema_version`、`toolpkg_id`、`version`、`api_version` 等。`docs/TOOLPKG_FORMAT_GUIDE.md:167`
- 主入口脚本由 `main` 字段指定，`subpackages` 列出子包。`docs/TOOLPKG_FORMAT_GUIDE.md:173`
- MCP 服务器接入后，`toToolPackage` 把它的工具转为标准 `ToolPackage`，分类记为 MCP。`app/src/main/java/com/ai/assistance/operit/core/tools/mcp/MCPPackage.kt:133`

## 内部分层

`core/tools` 按工具来源分层：顶层是 `AIToolHandler` 调度核心与集中注册；`defaultTool/` 为内置标准工具集；`system/` 提供系统级能力；`javascript/` 为 JS 脚本引擎；`packTool/` 管理 ToolPkg 包；`mcp/` 接入 MCP 服务器；`skill/` 管理技能包；另有 `agent/`、`calculator/` 等专用工具。`app/src/main/java/com/ai/assistance/operit/core/tools/AIToolHandler.kt:29`

## 关联条目

- 工具调用由聊天流程驱动，见 [[core-chat|聊天与消息处理]]。
- 工具数据模型位于数据层，见 [[data-model|数据模型]]。
- ToolPkg 的分发与市场侧，见 [[ext-plugins|插件与集成]]。<!-- confidence: INFERRED -->

## 来源

- `app/src/main/java/com/ai/assistance/operit/core/tools/`（调度核心、注册、执行器接口、钩子）
- `app/src/main/java/com/ai/assistance/operit/core/tools/mcp/`（MCP 接入）
- `app/src/main/java/com/ai/assistance/operit/core/tools/packTool/`（ToolPkg 包管理）
- `app/src/main/java/com/ai/assistance/operit/core/tools/skill/`（技能包）
- `app/src/main/java/com/ai/assistance/operit/core/tools/javascript/`（JS 引擎）
- `app/src/main/java/com/ai/assistance/operit/core/tools/defaultTool/`（内置标准工具）
- `app/src/main/java/com/ai/assistance/operit/core/tools/system/`（系统级能力）
- `app/src/main/java/com/ai/assistance/operit/core/tools/agent/`（专用工具）
- `app/src/main/java/com/ai/assistance/operit/data/model/AITool.kt`（工具数据模型）
- `app/src/main/java/com/ai/assistance/operit/api/chat/enhance/ToolExecutionManager.kt`（解析与批量执行）
- `docs/TOOLPKG_FORMAT_GUIDE.md`（ToolPkg 格式）
