---
title: 整体架构
module: app
sources: 9
date: 2026-09-30
---

# 整体架构

## 概述

Operit AI 是 Android 开源 AI Agent 平台，支持云端和本地模型，通过工具调用、工作流、ToolPkg、MCP、Skills 把模型接到 Android 系统能力、终端、浏览器、文件和项目工作空间（`README.md:36`）。仓库采用 Gradle 多模块结构，以 app 模块为绝对主体，原生能力经 JNI / CMake 集成。

## 模块划分

`settings.gradle.kts:20` 声明根项目名为 Operit，`settings.gradle.kts:21` 起通过 include 声明 9 个 Gradle 模块（`Repo_Arch_Basic.md:102`）：

| 模块 | 目录 | 职责 |
|---|---|---|
| app | `app/` | 主 Android 应用：界面、业务逻辑、资源、工具系统、项目模板、ObjectBox 模型，负责接入各本地原生能力（`Repo_Arch_Basic.md:32`） |
| dragonbones | `avator/dragonbones/` | DragonBones 骨骼动画：C++、OpenGL、JNI 提供加载渲染与动画控制（`Repo_Arch_Basic.md:48`） |
| fbx | `avator/fbx/` | FBX 原生运行时：ufbx C 库解析模型，CMake 从上游获取（`Repo_Arch_Basic.md:56`） |
| mmd | `avator/mmd/` | MMD 模型运行时与预览，含 Bullet3 等第三方组件（`Repo_Arch_Basic.md:72`；大纲注：端侧能力已停止维护，不再单独立页） |
| llama | `llm/llama/` | llama.cpp 原生集成：CMake/JNI 接入，提供 GGUF 本地推理（`Repo_Arch_Basic.md:68`；大纲注：端侧能力已停止维护，不再单独立页） |
| mnn | `llm/mnn/` | MNN 原生集成：CMake/Gradle 集成 Alibaba MNN，提供本地推理（`Repo_Arch_Basic.md:76`；大纲注：端侧能力已停止维护，不再单独立页） |
| terminal | （独立仓库） | OperitTerminalCore 的 git submodule，主仓库仅注册 `:terminal`（`.gitmodules:1`、`settings.gradle.kts:24`），详见 [[mod-terminal\|终端模块 TerminalCore]] |
| showerclient | `showerclient/` | Shower 虚拟显示客户端库：连接 Shower server、建虚拟显示、发触控按键、请求截图；宿主须注入 `ShellRunner`（`Repo_Arch_Basic.md:86`） |
| quickjs | `quickjs` | QuickJS JNI 模块，已接入 app（`app/build.gradle.kts:587`），详见 [[ext-quickjs\|QuickJS 脚本引擎]] |

模块名与目录名允许不同：`settings.gradle.kts:23` 用 `project(":dragonbones").projectDir = file("avator/dragonbones")` 把旧模块名映射到子目录，llm 下的 `:mnn`、`:llama` 同理。

## 依赖方向

1. 模块注册：`settings.gradle.kts:21` 起 9 个 `include` 声明全部模块（`settings.gradle.kts:21`）。
2. 依赖声明：`app/build.gradle.kts:580` 起 8 行 `implementation(project(...))` 把 dragonbones、terminal、mnn、llama、mmd、fbx、showerclient、quickjs 全部引入 app（`app/build.gradle.kts:580`）。
3. 逐文件核查其余 7 个模块的构建脚本（`avator/dragonbones/build.gradle.kts:1`、`avator/fbx/build.gradle.kts:1`、`avator/mmd/build.gradle.kts:1`、`llm/llama/build.gradle.kts:1`、`llm/mnn/build.gradle.kts:1`、`showerclient/build.gradle.kts:1`、`quickjs/build.gradle.kts:1`），均未发现 `project(...)` 依赖声明——Kotlin 层的模块间依赖边全部以 app 为起点，无横向或反向依赖。
4. web-chat 不在 Gradle 模块内：它是 React + Vite + TypeScript 前端，构建产物经同步脚本放入 `app/src/main/assets/web-chat`（`Repo_Arch_Basic.md:98`），详见 [[mod-webchat\|web-chat 前端]]。

## 为什么 app 占据绝大多数代码

1. 职责集中：应用界面、业务逻辑、Android 资源、工具系统、项目模板和 ObjectBox 模型全部位于 app（`Repo_Arch_Basic.md:32`）。
2. 唯一集成点：app 负责接入各个本地原生能力（`Repo_Arch_Basic.md:32`），并依赖全部 8 个兄弟模块（`app/build.gradle.kts:580`）。
3. 交付归属：最终 APK 的主要应用代码位于 app 目录（`Repo_Arch_Basic.md:32`）；包名 `com.ai.assistance.operit`、versionCode 51、versionName 1.12.2 均在 app 的构建脚本中定义（`app/build.gradle.kts:360`、`app/build.gradle.kts:401`）。

## Native 模块在 Kotlin 层为何几乎无依赖

1. Kotlin 侧只是薄封装：`avator/dragonbones/src/main/java/com/dragonbones/JniBridge.kt:5` 的 `object JniBridge` 在 init 中 `System.loadLibrary("dragonbones_native")`，以 `@JvmStatic external fun` 声明 JNI 入口；`avator/fbx/src/main/java/com/ai/assistance/fbx/FbxNative.kt:5` 的 `object FbxNative` 经 `FbxLibraryLoader.loadLibraries()` 加载后同样以 `external fun` 暴露能力。
2. 真正实现是 C/C++：fbx 经 ufbx C 库解析、由 CMake 从上游获取（`Repo_Arch_Basic.md:56`）；dragonbones 经 C++、OpenGL 实现（`Repo_Arch_Basic.md:48`）。
3. app 内同样模式：`app/src/main/java/com/ai/assistance/operit/util/ripgrep/NativeRipgrep.kt:9` 的 `internal object NativeRipgrep` 加载 `operit_ripgrep` 并声明 `external fun searchJson`。
4. 因此 native 模块之间没有 Kotlin 层调用关系：它们只被 app 单向 `implementation` 引入，虚拟形象侧的组装逻辑见 [[core-avatar\|虚拟形象]]。

## 来源

- `Repo_Arch_Basic.md`（根目录布局与模块职责原文）
- `settings.gradle.kts`（模块注册）
- `app/build.gradle.kts`（依赖方向、包名与版本）
- `README.md`（项目定位、系统要求、许可证）
- 关联引用：`.gitmodules`、`quickjs/README.md`、`avator/dragonbones/src/main/java/com/dragonbones/JniBridge.kt`、`avator/fbx/src/main/java/com/ai/assistance/fbx/FbxNative.kt`、`app/src/main/java/com/ai/assistance/operit/util/ripgrep/NativeRipgrep.kt`
