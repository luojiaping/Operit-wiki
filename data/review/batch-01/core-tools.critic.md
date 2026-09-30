---
critic: independent-session
page: core-tools
date: 2026-09-30
verdict: 需修改
---

# Critic 评审报告：工具系统（core-tools）

> 独立 critic session：只读了正文、facts.json，以及每个引用指向的代码行（±5 窗口）。
> 核验范围：facts.json 全部 33 条；正文禁用词 / frontmatter / 来源小节 / wikilink。

## 一、逐条事实判定

| # | 事实摘要 | ref | 判定 | 备注 |
|---|---------|-----|------|------|
| 1 | AITool 字段 name / parameters(默认[]) / description(默认"") | AITool.kt:12 | 支撑 | 12–16 行逐字一致 |
| 2 | ToolParameter 字段 name、value 均为 String | AITool.kt:8 | 支撑 | |
| 3 | ToolResult 字段 toolName / success / result(ToolResultData) / error(可空) | AITool.kt:29 | 支撑 | |
| 4 | ToolInvocation 字段 tool / rawText / responseLocation(IntRange) | AITool.kt:20 | 支撑 | |
| 5 | ToolValidationResult 字段 valid / errorMessage | AITool.kt:37 | 支撑 | |
| 6 | AIToolHandler 私有构造单例，getInstance 双重检查锁 | AIToolHandler.kt:29 | 支撑 | `private constructor`(29)；`fun getInstance`(36) 在窗口内，双重检查结构见 36–41 |
| 7 | availableTools 为 ConcurrentHashMap\<String, ToolExecutor\> 注册表 | AIToolHandler.kt:45 | 支撑 | 注释 "Available tools registry" 即在 44 行 |
| 8 | registerTool(name, descriptionGenerator?, executor) | AIToolHandler.kt:179 | 支撑 | descriptionGenerator 默认为 null，确为可选 |
| 9 | registerDefaultTools 用 AtomicBoolean+synchronized 双重检查，只注册一次，内调 registerAllTools | AIToolHandler.kt:211 | 支撑 | 212–216 行结构完整 |
| 10 | registerAllTools(handler, context) 定义于 ToolRegistration.kt | ToolRegistration.kt:36 | 支撑 | |
| 11 | getAllToolNames 返回键排序列表，供工具选择 UI 与工作流界面用 | AIToolHandler.kt:160 | 支撑（引用欠精确） | 排序逻辑支撑；"工具选择 UI"有 164–165 行注释佐证；"工作流界面"用途真实（WorkflowDetailScreen 确在调用），但不在引用 ±5 行内 |
| 12 | ToolExecutor：invoke 必实现；invokeAndStream 默认转调；validateParameters 默认有效 | AIToolHandler.kt:479 | 支撑 | 480/482/487–489 行逐项一致 |
| 13 | AIToolHook 生命周期回调（列出 5 个） | AIToolHook.kt:16 | 支撑 | 接口实际 7 个回调，事实列 5 个为子集陈述，无错误；onToolCallIntercept 默认 Allow、可返回 Block |
| 14 | executeTool 顺序：hook 拦截 → 取执行器 → 校验参数 → 执行 | AIToolHandler.kt:363 | 支撑 | 365/375/391/407 行顺序一致（以函数内相对行号核对） |
| 15 | executeToolAndStream 返回 Flow\<ToolResult\>，保留流式中间结果 | AIToolHandler.kt:419 | 支撑 | 注释原文 "preserves intermediate streaming results" |
| 16 | getToolExecutorOrActivate：缺失先补注册；packName:toolName 自动 usePackage | AIToolHandler.kt:303 | 支撑 | 注释 298–302 原文即此语义；实现 306–330 行一致 |
| 17 | extractToolInvocations 用 toolCallPattern 解析工具名、toolParamPattern 解析参数 | ToolExecutionManager.kt:306 | 支撑 | 实际调用在 321/326 行；流式 XML 分块解析（StreamXmlPlugin，311 行） |
| 18 | executeInvocations 先 registerDefaultTools，再做暴露模式拦截与角色卡权限拦截 | ToolExecutionManager.kt:504 | 支撑 | 520–522 注册；toolExposureMode 参数 510 行，多处实际拦截（219/227/236）；CharacterCardToolAccessResolver 528 行 |
| 19 | aggregateToolResults：success/error 取最后一个结果的值 | ToolExecutionManager.kt:710 | 支撑 | 730/732 行：`success = lastResult.success, error = lastResult.error` |
| 20 | .toolpkg 本质是标准 ZIP | TOOLPKG_FORMAT_GUIDE.md:11 | 支撑 | 原文 "本质上是一个标准的 ZIP 压缩包" |
| 21 | 必需文件：manifest.json + main.js | TOOLPKG_FORMAT_GUIDE.md:34 | 支撑 | 34–35 行均标"必需" |
| 22 | manifest 字段：schema_version / toolpkg_id / version / api_version / main / subpackages | TOOLPKG_FORMAT_GUIDE.md:165 | 存疑（引用越界） | 内容真实（165–175 行表），但 `main`(171)、`subpackages`(175) 超出 ref ±5；且 version/api_version 在表中"必需=否"，事实未注必需性虽不算错，但引用行 165 本身只覆盖 schema_version 一行 |
| 23 | MCPPackage.toToolPackage 转标准 ToolPackage，category=MCP，参数映射为 PackageToolParameter | MCPPackage.kt:133 | 支撑 | 注释 132 原文；实现含 `PackageToolParameter(` 与 `category = "MCP"` |
| 24 | MCPTool 字段 name / description / parameters | MCPTool.kt:9 | 支撑 | |
| 25 | MCPToolExecutor 实现 ToolExecutor | MCPToolExecutor.kt:23 | 支撑 | `class MCPToolExecutor(...) : ToolExecutor` |
| 26 | PackageManager.usePackage 激活包；getAvailablePackages / getAvailableServerPackages | PackageManager.kt:3246 | 存疑（引用越界） | usePackage 支撑（3246 行，注释 "Activates and loads"）；但 getAvailablePackages(3582)、getAvailableServerPackages(3434) 远在 ref ±5 之外 |
| 27 | packTool/ 核心类 PackageManager | PackageManager.kt:62 | 支撑 | |
| 28 | mcp/ 接入层，MCPToolExecutor 实现 ToolExecutor | MCPToolExecutor.kt:23 | 支撑 | |
| 29 | skill/ SkillManager 私有构造单例 | SkillManager.kt:12 | 支撑 | `private constructor` + INSTANCE 双重检查结构 |
| 30 | javascript/ JsEngine | JsEngine.kt:49 | 支撑 | 注释 "JavaScript 引擎 - 通过 QuickJS 执行" |
| 31 | defaultTool/standard/ 如 StandardShellToolExecutor | StandardShellToolExecutor.kt:18 | 支撑 | 目录归属正确；类注释为 ADB shell 工具（需 Shizuku），正文未展开此细节，不算错 |
| 32 | system/ 如 AndroidShellExecutor | AndroidShellExecutor.kt:11 | 支撑 | 注释"通过权限级别委托到相应的 Shell 执行器" |
| 33 | agent/ 下有 PhoneAgent | PhoneAgent.kt:119 | 支撑 | |

**重点抽查项结论**（任务指定三项）：

- **AIToolHandler 注册表机制**：全部支撑。单例（29/36）、ConcurrentHashMap 注册表（45）、registerTool 唯一登记入口（179）、registerDefaultTools 双重检查幂等（211）、getToolExecutorOrActivate 缺失补注册 + packName:toolName 自动激活（303）、executeTool 四步顺序（363）——与代码逐字相符。
- **ToolPkg manifest 必需字段**：内容真实但引用有瑕疵。必需文件 manifest.json + main.js（34–35）无误；字段表（165–175）中 version / api_version 实际为"必需=否"，事实与正文均未声称其必需，不构成事实错误；问题仅是 #22 的引用行覆盖不全。
- **MCPPackage.toToolPackage 转换关系**：支撑。转标准 ToolPackage、category="MCP"、MCP 参数→PackageToolParameter，三点在 133–165 行实现中全部找到。

## 二、正文检查

- **禁用词**：grep `可能/大概/似乎/应该/也许` —— 0 命中。通过。
- **Frontmatter**：title / module / sources / date 四项齐全。`sources: 15` = facts.json 中互不相同的引用文件数（15 个），与"来源"小节的 11 个条目（8 个目录 + 2 个文件 + 1 份指南）口径一致，无矛盾。
- **"来源"小节**：存在且非空，11 条，覆盖全部 seed 方向。
- **Wikilink**：`[[core-chat|聊天与消息处理]]`、`[[data-model|数据模型]]`、`[[ext-plugins|插件与集成]]` —— 均为"文件名|显示名"写法，符合图谱引擎按文件名解析的约定；ext-plugins 一行带了 `<!-- confidence: INFERRED -->`，标注正确（市场侧确为推测关联）。core-chat / data-model 为同批页面，ext-plugins 为规划页，前向链接可接受。
- **超出引用支撑的发挥**：未发现。概述句"注册、发现、执行全部收敛在 AIToolHandler 单例"有 29/45/363 行支撑；"经过拦截与权限检查"有 hook（16）与 executeInvocations（504–530）支撑；"结果回填进对话"有 replaceToolInvocation（233）支撑。内部分层一段的目录归属陈述均有对应事实（#27–#33）。
- **引用行准确性**：正文 ToolPkg 两处引用（:167、:173）比 facts.json 的 :165 更精确，无问题。

## 三、发现的问题（精确到行）

1. **facts.json #22**（`docs/TOOLPKG_FORMAT_GUIDE.md:165`）：断言含 `main`、`subpackages` 两个符号，实际在 171/175 行，超出"引用行 ±5 行内必须出现符号名"的铁律。修法：拆成两个引用（:165 覆盖 schema_version/toolpkg_id/version/api_version；:173 覆盖 main/subpackages），或改 ref 为 :170（±5 覆盖 165–175 全表）。
2. **facts.json #26**（`PackageManager.kt:3246`）：一条 ref 承载三个符号，`getAvailablePackages`(3582)、`getAvailableServerPackages`(3434) 远超 ±5。修法：拆成三条事实各带独立 ref，或 ref 改为多行引用。
3. **facts.json #11**（`AIToolHandler.kt:160`）："供工作流界面使用"用途子句真实（WorkflowDetailScreen 在用），但不在引用 ±5 行内。修法：删去该半句，或补第二引用。
4. （非阻塞备注）facts.json #13 AIToolHook 只列 5/7 个回调：子集陈述无事实错误，但正文"关键符号"节同样只提 onToolCallIntercept；建议正文补一句"另有 onToolPermissionChecked、onToolExecutionError 等回调"以免读者误以为穷尽。可选。

## 四、最终结论

**需修改** —— 事实层面 0 错误、无幻觉、无禁用词、无超引用发挥；3 处为引用精度问题（#22、#26 为引用铁律技术性违反，#11 为用途子句缺行内出处），均为 facts.json 侧的小修，不涉及正文重写。修完 1–3 条后可直接通过，无需打回。

问题数：3（需修改）+ 1（可选备注）。

## 修订记录（2026-09-30）
3 项必改已修：#22 manifest 字段 ref 改为 :170（覆盖 165–175）；#26 拆为三条独立引用（usePackage:3246、getAvailablePackages:3582、getAvailableServerPackages:3434）；#11 删去"供工作流界面使用"半句。另按可选备注补了 AIToolHook 其余回调说明。复跑 lint：硬失败 0，警告 0。结论更新为：通过。
