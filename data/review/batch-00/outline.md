---
title: Operit-wiki 大纲（草案）
module: meta
sources: [repo-map.json, dep-graph.json, modules.md]
date: 2026-09-30
---

# Operit-wiki 大纲（草案 v1）

> 生成依据：阶段 0 确定性脚本统计（`scripts/repo_map.py`），全部数字来自实际扫描，未做推测。
> 仓库事实：**app 模块占 1362/1402 个 kt 文件、4961/5039 个符号**，是绝对主体；其余 8 个模块合计 40 个 kt 文件。

## 章节与页面（共 24 页）

### 架构总览
1. **整体架构** —— 模块划分、依赖方向（全部以 app 为起点）、native 模块在 Kotlin 层为何几乎无依赖

### Agent 核心
2. **工具系统** —— 工具定义/注册/发现、调用链路、ToolPkg 格式（`core/tools`，185 文件）
3. **聊天与消息处理** —— 消息处理链、各 Delegate 分工、多轮任务状态机
4. **工作流引擎** —— 定义格式、执行语义、与单次工具调用的区别
5. **虚拟形象（Avatar）** —— 子系统边界、dragonbones/mmd/fbx 分工、Kotlin→native 调用
6. **配置体系** —— 配置分层、UI→preferences→生效链路

### 模型接入
7. **云端 Chat API 接入** —— 渠道扩展、流式响应链路（`api/chat`，110 文件）
8. **语音能力（ASR/TTS）** —— 识别/合成链路、与聊天流程衔接
9. **第三方 OAuth 接入** —— Codex/GitHub 授权流程、token 存储刷新
10. **端侧推理（llama/mnn）** —— 双模块分工、模型加载、JNI 边界

### 数据层
11. **数据模型** —— 会话/消息/工具调用记录、数据库选型
12. **MCP 集成** —— server 配置连接、MCP 工具汇入工具系统
13. **备份、恢复与导出** —— 数据范围格式、恢复导出链路

### 界面
14. **聊天界面** —— 组件与状态管理（`features/chat`，175 文件）
15. **设置界面** —— 信息架构、与配置体系绑定
16. **工具箱与技能包界面** —— 两者区别、技能包安装管理链路
17. **悬浮窗与主界面框架** —— 悬浮窗权限生命周期、主界面导航
18. **其他功能页** —— memory/websession/assistant/tokenstats

### 脚本与扩展
19. **QuickJS 脚本引擎** —— 角色、脚本能力边界、安全边界
20. **插件与集成** —— plugins vs integrations、第三方开发插件流程

### 周边模块
21. **Shower 客户端库** —— 按 README 职责、app→showerclient 依赖
22. **web-chat 前端** —— Vite+TS 项目定位、与 Android 端关系
23. **terminal 模块（空模块说明）** —— settings 注册但 0 文件，需人工确认意图

### 附录
24. **工具类与后台服务** —— util 分组、services 触发条件

## 请你重点评审

1. 章节切分是否合理？有没有漏掉你关心的部分？
2. `terminal` 空模块：保留一页说明还是直接不列？
3. `ui/features` 下 21 个功能目录合并为 5 页，粒度合适吗？
4. 以下模块职责脚本找不到出处，标了"未知，需人工确认"，你方便各补一句话吗：**app、mnn、llama、mmd、fbx**

## 来源

- `wiki-work/repo-map.json`（3067 文件 / 1402 kt / 5039 顶层符号，零声明文件 0%）
- `wiki-work/dep-graph.json`（8 条模块依赖边，全部以 app 为起点）
- `wiki-work/modules.md`
- `~/workspace/Operit/Repo_Arch_Basic.md`、`README.md`（项目介绍原文引用）
