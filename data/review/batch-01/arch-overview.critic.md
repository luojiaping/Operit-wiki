# Critic 评审报告：arch-overview（整体架构）

- 评审对象：`review/batch-01/arch-overview.md` + `wiki-work/facts/batch-01/arch-overview.facts.json`（26 条事实）
- 评审人：独立 critic（全新 session）
- 依据：`SCHEMA.md` 引用铁律 / 禁用词 / 评审标准
- 机器 lint（`--src ~/workspace/Operit --dir review/batch-01`）：0 硬失败，0 警告

## 一、逐条事实判定

| # | 事实摘要 | ref | 判定 | 说明 |
|---|---|---|---|---|
| 1 | 根项目名为 Operit | settings.gradle.kts:20 | 支撑 | `rootProject.name = "Operit"` 逐字相符 |
| 2 | 9 个 Gradle 模块列表 | settings.gradle.kts:21 | 支撑 | 引用为块起始行；9 个 include 分布在 21–34 行，已逐行核验齐全 |
| 3 | dragonbones projectDir → avator/dragonbones | settings.gradle.kts:23 | 支撑 | `project(":dragonbones").projectDir = file("avator/dragonbones")` 逐字相符 |
| 4 | terminal 是 OperitTerminalCore 的 git submodule | .gitmodules:1 | 支撑 | `[submodule "terminal"]` + url 指向 OperitTerminalCore；主仓库 terminal/ 目录为空 |
| 5 | Repo_Arch_Basic 列出 9 模块 | Repo_Arch_Basic.md:102 | 支撑 | 102 行正是"相关说明"模块列表条目 |
| 6 | app 是主 Android 应用模块 | Repo_Arch_Basic.md:32 | 支撑 | ±5 行内为 app 章节原文，职责描述逐字相符 |
| 7 | app 依赖全部 8 个兄弟模块 | app/build.gradle.kts:580 | 支撑 | 580–587 行 8 条 `implementation(project(...))`，与事实列出的 8 个名字一致 |
| 8 | namespace 为 com.ai.assistance.operit | app/build.gradle.kts:360 | 支撑 | ±5 行内 `namespace = "com.ai.assistance.operit"` |
| 9 | applicationId / versionCode 51 / versionName 1.12.2 | app/build.gradle.kts:401 | 支撑 | defaultConfig 块三值逐字相符 |
| 10 | showerclient 职责 | Repo_Arch_Basic.md:86 | 支撑 | 与文档原文逐字相符 |
| 11 | web-chat 构建产物同步进 assets | Repo_Arch_Basic.md:98 | 支撑 | 与文档原文逐字相符 |
| 12 | quickjs 尚未接入 app | Repo_Arch_Basic.md:82 | **不支撑** | 引用文档确有此句，但文档已过时。**构建文件证伪**：`app/build.gradle.kts:587` 有 `implementation(project(":quickjs"))`；且 app 内 `core/tools/javascript/JsEngine.kt` 等实际引用 quickjs 类。quickjs 已接入。 |
| 13 | QuickJsNativeCompatScriptBuilder 只落在 quickjs 目录、未接 app | quickjs/README.md:12 | **不支撑** | 同 #12，"还没有接到 app 模块"已被构建依赖与代码引用证伪 |
| 14 | dragonbones 经 C++/OpenGL/JNI | Repo_Arch_Basic.md:48 | 支撑 | 与文档原文逐字相符 |
| 15 | fbx 经 ufbx C 库、CMake 获取上游 | Repo_Arch_Basic.md:56 | 支撑 | 与文档原文逐字相符 |
| 16 | JniBridge 薄封装 | JniBridge.kt:5 | 支撑 | 5 行 `System.loadLibrary("dragonbones_native")`，3 行 `object JniBridge`，8 行 `@JvmStatic external fun` |
| 17 | FbxNative 薄封装 | FbxNative.kt:5 | 支撑 | 6 行 `FbxLibraryLoader.loadLibraries()`，9 行 `@JvmStatic external fun nativeIsAvailable` |
| 18 | NativeRipgrep 同样模式 | NativeRipgrep.kt:9 | 支撑 | 5 行 loadLibrary("operit_ripgrep")，9 行 `external fun searchJson` |
| 19 | Operit AI 平台定位 | README.md:36 | 支撑 | 英文原文的准确意译，无添油加醋 |
| 20 | 系统要求 Android 8.0+ / ARM64 | README.md:153 | 支撑 | 表格原文逐字相符 |
| 21 | 主代码 LGPL v3 | README.md:229 | 支撑 | License 章节原文逐字相符 |
| 22 | Operit 2 是第二代跨平台实现 | README.md:40 | **存疑** | 内容为真，但出处不在 :40。正确位置是 **README.md:26–28**（"Operit 2: Operit's Cross-Platform Successor"，shared Rust runtime / Flutter clients）。:40±5 行内无相关内容，引用行号错误 |
| 23 | 最终 APK 主要代码在 app | Repo_Arch_Basic.md:32 | 支撑 | 与 #6 同源，文档原文有此句 |
| 24 | llama 原生集成 | Repo_Arch_Basic.md:68 | 支撑 | 与文档原文逐字相符 |
| 25 | mmd 运行时与预览 | Repo_Arch_Basic.md:72 | 支撑 | 与文档原文逐字相符 |
| 26 | mnn 原生集成 | Repo_Arch_Basic.md:76 | 支撑 | 与文档原文逐字相符 |

判定统计：支撑 23 / 不支撑 2（#12、#13）/ 存疑 1（#22）。

## 二、正文检查

- **禁用词**：`可能/大概/似乎/应该/也许` 全文零命中 ✓
- **frontmatter**：title / module / sources / date 齐全 ✓
- **"来源"小节**：存在且非空，列出 9 项 ✓
- **wikilink**：4 处（`[[mod-terminal|…]]`、`[[ext-quickjs|…]]`、`[[mod-webchat|…]]`、`[[core-avatar|…]]`）格式均为 `[[id|label]]`，目标 id 均为大纲 v2 规划页；对应 md 尚未生成，符合"规划中"条目约定，不判断链 ✓

### 发现的问题

**P0-1（事实错误，且与正文自相矛盾）——正文第 28 行**
模块表 quickjs 行写"当前 README 明确尚未接入 app"。该说法已被构建文件证伪（`app/build.gradle.kts:587`），且与本页"依赖方向"第 2 条（第 34 行："8 行 implementation(project(...)) 把 …… quickjs 全部引入 app"）**直接矛盾**。同一页内两处说法互斥，必须改。对应 facts.json #12、#13 亦须修正或删除（写作者轻信了过时文档，未以构建文件为准）。

**P1-2（无引用断言）——正文第 36 行**
"经核查，其余 7 个模块各自的 build.gradle.kts 均未声明 project(...) 依赖——Kotlin 层的模块间依赖边全部以 app 为起点，无横向或反向依赖。"
critic 实测：有构建文件的 7 个模块确为 0 处 `project(` 依赖（terminal 目录为空、无构建文件），内容为真。但该断言**不在 facts.json 中**，正文也**无任何引用**，违反引用铁律（每个事实断言必须附引用；写作只许复述已验证事实）。需补引用（如引 dep-graph.json 或各 build.gradle.kts）或先入 facts 再写。

**P1-3（无引用数字）——正文第 39 行小节标题**
"为什么 app 占 97% 的 Kotlin 代码"——"97%" 在正文无引用（数据出自阶段 0 `repo-map.json`，正文未引）。需补引用或删具体数字。

**P2-4（facts 引用行号错误，不影响正文）**
facts.json #22 引用 `README.md:40` 错误，正确为 `README.md:26–28`。该事实正文未采用，不影响页面，但 facts 入库前应修正。

## 三、最终结论

**需修改**

修改清单：
1. 正文第 28 行：删除"尚未接入 app"错误表述，改为 quickjs 已被 app 依赖引入（`app/build.gradle.kts:587`），实际使用见 `core/tools/javascript/`；facts.json #12、#13 同步修正或删除。
2. 正文第 36 行：为"无横向/反向依赖"断言补引用（或先补 facts 条目再引用）。
3. 正文第 39 行：为"97%"补 `repo-map.json` 引用，或改为无数字表述。
4. facts.json #22：ref 改为 `README.md:26`（或 26–28）。

说明：23/26 事实支撑扎实，结构合规、无禁用词、无幻觉发挥，lint 零失败，故不打回重写；但 P0-1 是事实性错误且自相矛盾，必须修改后才能进入评审。

## 修订记录（2026-09-30）
4 项问题已修：P0 quickjs"尚未接入 app"为过期 README 误导，已改为"已接入"（app/build.gradle.kts:587 的 implementation 声明 + app 的 JsEngine 持有 quickjs 模块的 OperitQuickJsEngine 实例），facts #12/#13 重写并增补定义位置事实；P1 第 36 行"无横向依赖"补 7 个模块构建脚本的行级引用；P1 "97%" 标题去数字；P2 facts #22 行号改 README.md:27。复跑 lint：硬失败 0，警告 0。结论更新为：通过。
