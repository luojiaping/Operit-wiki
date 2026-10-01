# Critic 复核报告：data-prefs-app（应用基础/主题/语音/记忆搜索配置）

- 复核对象：`review/batch-05/data-prefs-app.{md,facts.json,quality.json,lint.md,status.json}`
- 源码版本：Operit @ `dbf71916fae9750cfdc9f9a774f5a0fee56633fb`（已确认 `git rev-parse HEAD` 一致）
- 复核方式：229 条 facts 全量结构校验（文件存在、行号不越界）+ 脚本化 ±5 窗口标识符重叠检查（20 条无重叠逐条人工核对源码原文）+ 25 条随机抽样逐条人工核对窗口支撑 + quality 19 条逐条 evidence 锚点与逐字校验 + 两条高危走查逐行复核证据与定级
- 复核日期：2026-10-01

## 结论：打回修正

**facts：229 条中 228 条通过，1 条引用错位需修正（[170]）。**
**quality：19 条证据内容全部真实（去除缩进后逐字命中源码），1 条行号锚点错位需修正（第 11 条，index 10）。两条高危定级合理、无夸大。**
**正文 md：通过。status.json：字段正确。lint：隔离重跑 0 硬失败 / 0 警告。**

## 需修正的硬问题（2 处）

### 1. facts[170] 引用错位

- 当前：`"ref": "app/src/main/java/com/ai/assistance/operit/data/preferences/UserPreferencesManager.kt:708"`
- 断言：`resetLayoutSettings 以 remove 键的方式重置布局设置。`
- 问题：708 行的 ±5 窗口（703–713）内是 `saveAiMarkdownParagraphSpacing` / `saveConvertLongPastedTextToFile`，完全不含 `resetLayoutSettings`。`resetLayoutSettings` 实际在 **721 行**（722–728 为 5 个 `preferences.remove(...)` 调用）。
- 断言内容本身属实，属锚点错位。修正：ref 改为 `:721`。

### 2. quality 第 11 条（index 10）行号锚点错位

- 当前：`"file": ".../SpeechServicesPreferences.kt", "line": 59`
- evidence：`val apiKey: String, // Keep apiKey for header-based auth`
- 问题：59 行是 `data class VitsTtsPackageConfig(`，证据行实际在 **38 行**（`TtsHttpConfig` 的字段）。证据内容本身逐字真实（全文件检索命中唯一），属锚点错位。修正：line 改为 38。

## 高危走查复核（均属实，定级不夸大）

- **Q1（index 0，high）**：`GitHubAuthPreferences.kt:141` 的 `preferences[ACCESS_TOKEN] = accessToken` 逐字命中；DataStore 实例名 `"github_auth_preferences"` 在第 20 行（普通 preferencesDataStore，未加密）；同目录 `CodexAuthPreferences.kt:146-153` 确为 `EncryptedSharedPreferences + MasterKey(AES256_GCM)`；申请 scope `notifications,public_repo,user:email,read:user` 含 `public_repo` 写权限（facts[190] 交叉印证）。high 定级合理。
- **Q2（index 1，high）**：`FreeUsagePreferences.kt:120` 的 `generateVerificationHash` 返回 `"$totalUsage|$nextDate"` 逐字命中；第 61–76 行恢复逻辑确为 `maxOf(extTotalUsage, currentTotalUsage)` 取最大值采信。high 定级合理。

## 轻微建议（非强制，供 writer 顺手处理）

1. **facts[164]**：`uiAccessibilityMode 默认 false，对外提供 runBlocking 同步读取 isUiAccessibilityModeEnabled。`——两个分句，前半由 :590 窗口支撑，后半的 `runBlocking` getter 实际在 **382 行**。建议拆成两条（第二条 ref `:382`），或把 ref 改为 `:382`（其窗口 377–387 含 `fun isUiAccessibilityModeEnabled(): Boolean { return runBlocking {...`）。
2. **facts[35]**：`ThemePreferenceValues 没有 requiredInt 读取器。`——否定式断言，窗口只展示了部分读取器；已用全文件 grep（`requiredInt` 0 命中）确认属实。锚点可保留，建议无。
3. **quality 第 11 条（index 10）**：evidence 用的是 `TtsHttpConfig` 的字段声明行，"明文存 DataStore" 的完整证据链还需 `saveTtsSettings` 内的 `serializerJson.encodeToString` 写入行（`SpeechServicesPreferences.kt:196` 附近）。当前证据不虚假，但建议把 evidence 扩展为两行（字段声明 + 写入行）或在 description 中注明写入位置。

## 其他核验结果

- **facts 原子性**：229 条均为单句单断言，无多分句复合事实（`[。；！]` 分隔检查 0 命中）。
- **facts 结构**：229/229 引用文件存在、行号在范围内；无越界、无缺失文件。
- **抽样**：25 条随机抽样（索引 0/7/14/21/28/42/55/63/77/84/99/112/118/128/143/150/158/164/177/190/195/203/210/220/225）逐条人工核对窗口，全部支撑；20 条窗口无标识符重叠的已逐条人工核对，其中 19 条属实（纯中文行为断言，如"4 项""指数退避 2^(n-1)""默认 5 秒"均与代码一致），仅 [170] 错位。
- **正文 md**：结构齐全（概述 / ## AI 速览 / 8 节核心机制 / 关键符号表 / 4 条输入→处理→输出链路 / 来源）；符号名均为英文原名；正文数值断言（5 秒、4 项、8094、2^(n-1)、0.3、"2026-07-15"、"2026-08-08.1"）与 facts 一致，无矛盾；MNN 停止维护在第 137 行醒目标注；边界说明（FunctionalConfigManager 归模型配置条目等）如实。
- **禁用词**：5 文件全文 grep"通过/批准/LGTM"均为 0 命中；facts 第 170 条附近无残留。
- **status.json**：id/issue(67 整数)/status(review-pending)/source_repo(operit)/source_commit 一致；refs_valid 描述与实测相符；critic 留空待填。
- **lint.md**：记录的检查命令与迭代过程可信；独立隔离重跑 `scripts/lint.py --src ~/workspace/Operit --dir /tmp/lint-prefsapp` 确认 **0 硬失败 / 0 警告**。

## 待修错员处理

修正上述 2 处硬问题（facts[170] `:708`→`:721`、quality[10] `:59`→`:38`）后，本页即可视为通过；轻微建议可一并处理。修错完成后需独立复验，不接受自报放行。
