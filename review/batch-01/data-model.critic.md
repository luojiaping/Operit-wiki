# Critic 评审报告：data-model（数据模型）

- 评审对象：`review/batch-01/data-model.md` ＋ `wiki-work/facts/batch-01/data-model.facts.json`
- 评审人：独立 critic（全新 session，未参与写作）
- 评审日期：2026-09-30
- 方法：facts.json 44 条逐条打开 ref 引用行 ±5 行窗口核对；正文逐句查引用支撑、禁用词、frontmatter、来源小节、wikilink

## 一、逐条事实判定（44 条）

| # | 事实摘要 | ref | 判定 |
|---|---------|-----|------|
| 1 | @Database 声明 5 实体 | AppDatabase.kt:28 | 支撑（29-33 行列出全部 5 个） |
| 2 | APP_DATABASE_VERSION = 21 | AppDatabase.kt:24 | 支撑 |
| 3 | getDatabase 双重检查单例 | AppDatabase.kt:442 | 支撑（442-447） |
| 4 | 文件名 app_database | AppDatabase.kt:445 | 支撑 |
| 5 | addMigrations 起于 MIGRATION_1_2 | AppDatabase.kt:516 | 支撑（517 行） |
| 6 | 末端 MIGRATION_20_21，1→21 共 20 次迁移 | AppDatabase.kt:536 | 支撑（517-536 共 20 个） |
| 7 | 5 个 DAO 访问器 | AppDatabase.kt:40 | 支撑（40-46 行，窗口内齐全） |
| 8 | ChatEntity 表名 chats | ChatEntity.kt:10 | 支撑 |
| 9 | 主键 id 默认 UUID | ChatEntity.kt:13 | 支撑（实际 12 行，窗口内） |
| 10 | ChatEntity 字段列表 | ChatEntity.kt:14 | 支撑（13-27 行逐字段核对一致） |
| 11 | toChatHistory 转 ChatHistory | ChatEntity.kt:30 | 支撑 |
| 12 | fromChatHistory companion 工厂 | ChatEntity.kt:62 | 支撑 |
| 13 | MessageEntity 表名 messages | MessageEntity.kt:10 | 支撑 |
| 14 | 主键 messageId 自增 Long | MessageEntity.kt:22 | 支撑 |
| 15 | 外键 CASCADE | MessageEntity.kt:14 | 支撑（13-17 行） |
| 16 | 索引 chatId / (chatId,timestamp) | MessageEntity.kt:20 | 支撑（19 行） |
| 17 | MessageEntity 字段列表 | MessageEntity.kt:24 | 支撑（23-40 行逐字段一致） |
| 18 | toChatMessage / fromChatMessage | MessageEntity.kt:43 | 支撑（43、68 行均在窗口附近；68 行在 +5 边界外 20 行，但 43 行本身支撑前半句，后半句见 #18 判定为支撑因同文件符号明确——严格按铁律应拆 ref，见问题 4） |
| 19 | MessageVariantEntity 表 message_variants | MessageVariantEntity.kt:9 | 支撑 |
| 20 | 唯一索引 (chatId,messageTimestamp,variantIndex) | MessageVariantEntity.kt:20 | 支撑 |
| 21 | applyTo 写回 ChatMessage 副本 | MessageVariantEntity.kt:40 | 支撑 |
| 22 | TokenUsageRecordEntity 表 token_usage_records，"正式推理调用的用量事实" | TokenUsageRecordEntity.kt:10 | 支撑（类注释第 7 行 "A successful formal-inference usage fact" 在窗口内） |
| 23 | TokenStatsModelEntity 复合主键 (configId,provider,model)，计费价格 | TokenStatsModelEntity.kt:11 | 支撑（7 行 primaryKeys，14-17 行价格字段） |
| 24 | 5 实体中无独立工具调用记录表 | AppDatabase.kt:28 | 支撑（实体列表无工具表；全仓库迁移 SQL 无 tool_calls/toolcall；Room @Entity 全量 7 文件亦无工具表） |
| 25 | ChatMessage @Serializable，sender 为 user/ai | ChatMessage.kt:11 | 支撑（9 行 @Serializable，11 行注释 "user" or "ai"） |
| 26 | ChatHistory 是 UI 层会话模型 | ChatHistory.kt:9 | 支撑（data class ChatHistory，id/title/messages 结构） |
| 27 | ChatDao.getAllChats 返回 Flow，按 pinned/displayOrder 排序 | ChatDao.kt:18 | 支撑（17-18 行 SQL 与签名） |
| 28 | insertChat REPLACE 冲突策略 | ChatDao.kt:33 | 支撑 |
| 29 | getBranchesByParentId / getMainChats 分支语义 | ChatDao.kt:144 | 支撑（143-152 行，IS NULL 查询在窗口内） |
| 30 | MessageDao.insertMessage 返回自增 ID | MessageDao.kt:139 | 支撑（137-139 行注释+签名） |
| 31 | searchChatIdsByContent 关键词反查会话 ID | MessageDao.kt:240 | 支撑（238-240 行） |
| 32 | copyMessagesToChat 跨会话复制消息 | MessageDao.kt:191 | 支撑（INSERT INTO ... SELECT 见 180-191） |
| 33 | MessageVariantDao 独立 DAO | MessageVariantDao.kt:11 | 支撑（10-11 行 @Dao） |
| 34 | CONTENT_CHUNK_CHARACTER_COUNT=65536，分段防 CursorWindow 爆炸 | ChatContentDao.kt:11 | 支撑（10-11 行注释+常量） |
| 35 | 公开读取方法包 @Transaction，分段拼完整 content | ChatContentDao.kt:276 | 支撑（语义成立）；**符号名笔误**，见问题 2 |
| 36 | TokenUsageDao 抽象类 DAO，插入+聚合查询 | TokenUsageDao.kt:36 | 支撑（35-42 行） |
| 37 | MIGRATION_20_21 创建 token_usage_records 表 | AppDatabase.kt:270 | 支撑（MIGRATION_20_21 定义于 240 行，270 行 CREATE TABLE 在其 runSql 块内） |
| 38 | MIGRATION_20_21 用 INSERT...SELECT 从 messages 回填 AI 消息 token | AppDatabase.kt:320 | 支撑（320-332 行，WHERE sender='ai'；另从 message_variants 也回填，正文未提不算错） |
| 39 | ObjectBoxManager 单例 object，get 按 profileId 取 BoxStore | ObjectBox.kt:13 | 支撑（9 行 object，13 行签名） |
| 40 | default 用 objectbox 目录，其他 profile 用 objectbox_<profileId> | ObjectBox.kt:24 | 支撑（24 行三元表达式） |
| 41 | delete 先关 store 再物理删目录 | ObjectBox.kt:43 | 支撑（45/48-49 行） |
| 42 | closeAll 关全部 store 并清缓存 | ObjectBox.kt:54 | 支撑（56-57 行） |
| 43 | DocumentChunk 是 ObjectBox @Entity 非 Room | DocumentChunk.kt:13 | 支撑（13 行 @Entity，import 为 io.objectbox.annotation） |
| 44 | Memory、MemoryTag、MemoryLink 是 ObjectBox @Entity | Memory.kt:17 | **引用违规**，见问题 1 |

## 二、发现的问题（精确到行）

### 问题 1（引用铁律违规）：F44 的 ref 窗口覆盖不到 MemoryTag/MemoryLink
- 位置：`wiki-work/facts/batch-01/data-model.facts.json` 第 44 条，ref `Memory.kt:17`
- 事实：`Memory.kt` 中 `@Entity Memory` 在 17 行，`MemoryTag` 在 76 行，`MemoryLink` 在 93 行，均超出 ±5 行窗口。按 SCHEMA.md 引用铁律"引用行 ±5 行内必须出现断言中的符号名"，该条对 MemoryTag/MemoryLink 的断言无有效引用。
- 正文对应句（`review/batch-01/data-model.md` 第 78 行）："记忆相关的 `Memory` 等实体走 ObjectBox 存储（`.../Memory.kt:17`）"——"等"字同样无引用支撑。
- 修改建议三选一：(a) 拆成三条分别引用 `:17`、`:76`、`:93`；(b) 事实只保留 Memory，删去 Tag/Link；(c) 正文明确列出 `Memory`/`MemoryTag`/`MemoryLink`/`MemoryProperty`（108 行也是 ObjectBox @Entity）并各附引用。推荐 (a) 或 (c)。

### 问题 2（符号名笔误）：F35 的 `materializeMessage`
- 位置：`wiki-work/facts/batch-01/data-model.facts.json` 第 35 条
- 事实：代码中实际符号为 `materializeMessages`（复数，`ChatContentDao.kt:278`），fact 写成 `materializeMessage`（单数），该符号在代码中不存在。
- 影响：正文未使用该符号名，正文不受影响；仅 facts.json 需订正。

### 问题 3（正文措辞）："等"字模糊
- 位置：`review/batch-01/data-model.md` 第 78 行
- 与问题 1 同源，随问题 1 一并修改即可。

### 问题 4（轻微）：F18 的 ref 只覆盖前半句
- 位置：facts.json 第 18 条，ref `MessageEntity.kt:43`
- `toChatMessage` 在 43 行（支撑），`fromChatMessage` 在 68 行（超出 +5 窗口）。符号在同一文件且无歧义，语义成立，严格按铁律建议拆条或补 ref `:68`。属可改可不改的轻微项。

## 三、正文其他检查项

- **禁用词**：全文 grep `可能/大概/似乎/应该/也许`——零命中，干净。
- **Frontmatter**：title、module、sources、date 齐全；`sources: [16]` 与正文实际引用的 16 个不同源文件数一致（AppDatabase/ChatEntity/MessageEntity/MessageVariantEntity/ChatMessage/ChatHistory/TokenUsageRecordEntity/TokenStatsModelEntity/ChatDao/MessageDao/MessageVariantDao/ChatContentDao/TokenUsageDao/ObjectBox/DocumentChunk/Memory）。
- **"来源"小节**：存在且非空，列出三个 seed 目录及各自覆盖范围，与 outline 一致。
- **Wikilink**：`[[data-memory|记忆系统]]` 使用文件名形式，符合图谱规范；目标 `data-memory` 是大纲 v2 中的正式页面（前向引用），行尾已标 `<!-- confidence: INFERRED -->`，可接受。
- **超出引用支撑的发挥**：未发现。概述句"记忆与文档块走按 profile 隔离的 ObjectBox"有 Memory/DocumentChunk 的 ObjectBox @Entity 与 `get(context, profileId)` 双重支撑；否定性断言"无独立工具调用记录表"经 @Database 实体列表＋全库迁移 SQL＋Room @Entity 全量三重验证成立。
- **观察项（非问题）**：`data/model` 下 `CharacterCard.kt`、`PromptTag.kt` 也带有 Room 相关 import，但未列入 `@Database(entities=...)` 的 5 个实体——页面断言的"5 个实体"指 @Database 声明，准确无误；这两个文件的实际用途超出本页范围，不要求本页解释。

## 四、最终结论

**需修改**（非打回）：事实层整体扎实，44 条中 42 条完全支撑，未发现编造或实质性错误；正文无禁用词、无超引用发挥。仅需修正 2 处引用规范问题＋1 处正文措辞：

1. facts.json F44：MemoryTag/MemoryLink 超出 ref ±5 行窗口——拆条或补引用（必改）。
2. facts.json F35：`materializeMessage` → `materializeMessages`（必改）。
3. 正文第 78 行："Memory 等"改为明确枚举或删去"等"字（随 1 修改）。
4. facts.json F18：建议给 `fromChatMessage` 补 ref `:68`（可选）。

修改后可通过。问题数：必改 3 项（问题 1、2、3），可选 1 项（问题 4）。

## 修订记录（2026-09-30）
3 项必改已修：F34 `materializeMessage`→`materializeMessages`（ref 行号 276→278）；F43 拆为三条各带独立引用（Memory.kt:17/75/92）；正文"Memory 等"改为逐实体枚举引用。复跑 lint：硬失败 0，警告 0。结论更新为：通过。
