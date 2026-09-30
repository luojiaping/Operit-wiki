---
title: 数据模型
module: app
sources: [16]
date: 2026-09-30
---

# 数据模型

## 概述

Operit 聊天数据的持久化层：会话、消息、消息版本与 token 用量存于 Room（SQLite）数据库，记忆与文档块走按 profile 隔离的 ObjectBox；Room 侧单例入口是 `getDatabase`，物理文件名为 `app_database`（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:442`）。

## 关键符号

### 数据库选型

- `AppDatabase` 继承 `RoomDatabase`，是全应用唯一的数据库抽象类（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:37`）。
- `@Database` 注解声明 5 个实体：`ChatEntity`、`MessageEntity`、`MessageVariantEntity`、`TokenUsageRecordEntity`、`TokenStatsModelEntity`（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:28`）。
- 数据库版本 `APP_DATABASE_VERSION` 为 21（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:24`）。
- `addMigrations` 注册从 `MIGRATION_1_2` 起的连续版本迁移（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:516`）。
- 迁移链末端 `MIGRATION_20_21`，版本 1→21 共 20 次迁移（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:536`）。
- DAO 访问器：`chatDao`、`messageDao`（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:40`）。
- `messageVariantDao`、`chatContentDao`、`tokenUsageDao`（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:44`）。
- `ObjectBoxManager.get` 按 `profileId` 获取 `BoxStore`（`app/src/main/java/com/ai/assistance/operit/data/db/ObjectBox.kt:13`）。
- default 用目录 `objectbox`，其他 profile 用 `objectbox_<profileId>`（`app/src/main/java/com/ai/assistance/operit/data/db/ObjectBox.kt:24`）。
- `delete` 先关闭 store 再物理删除数据库目录（`app/src/main/java/com/ai/assistance/operit/data/db/ObjectBox.kt:43`）。
- `closeAll` 关闭全部 store 并清空 `stores` 缓存（`app/src/main/java/com/ai/assistance/operit/data/db/ObjectBox.kt:54`）。

### 会话与消息实体

- 会话实体映射 `chats` 表（`app/src/main/java/com/ai/assistance/operit/data/model/ChatEntity.kt:10`）；主键 `id` 默认为 `UUID.randomUUID().toString()`（`app/src/main/java/com/ai/assistance/operit/data/model/ChatEntity.kt:12`）。
- `ChatEntity` 字段覆盖标题、创建/更新时间、输入/输出 token 计数、分组、显示顺序、工作区、父会话、角色卡绑定、锁定与置顶（`app/src/main/java/com/ai/assistance/operit/data/model/ChatEntity.kt:13`）。
- `toChatHistory` 把实体转为 UI 层 `ChatHistory`（`app/src/main/java/com/ai/assistance/operit/data/model/ChatEntity.kt:30`）。
- companion 的 `fromChatHistory` 反向构造实体（`app/src/main/java/com/ai/assistance/operit/data/model/ChatEntity.kt:62`）。
- 消息实体映射 `messages` 表（`app/src/main/java/com/ai/assistance/operit/data/model/MessageEntity.kt:10`）。
- `MessageEntity` 声明自增主键 `messageId`（`app/src/main/java/com/ai/assistance/operit/data/model/MessageEntity.kt:23`）。
- 外键以 `chatId` 关联会话，`onDelete = CASCADE`，删除会话时级联删除消息（`app/src/main/java/com/ai/assistance/operit/data/model/MessageEntity.kt:14`）；索引建在 `chatId` 与（`chatId`，`timestamp`）上（`app/src/main/java/com/ai/assistance/operit/data/model/MessageEntity.kt:20`）。
- `MessageEntity` 字段覆盖发送方、正文、时间戳、排序号、角色名、选中版本序号、供应商、模型名、token 计数、耗时与收藏标记（`app/src/main/java/com/ai/assistance/operit/data/model/MessageEntity.kt:24`）。
- `toChatMessage` 把实体转为运行时 `ChatMessage`（`app/src/main/java/com/ai/assistance/operit/data/model/MessageEntity.kt:43`）。
- `fromChatMessage` 是 companion 反向工厂函数（`app/src/main/java/com/ai/assistance/operit/data/model/MessageEntity.kt:68`）。
- 消息版本实体映射 `message_variants` 表，存同一条消息的多个回答版本（`app/src/main/java/com/ai/assistance/operit/data/model/MessageVariantEntity.kt:9`）。
- `MessageVariantEntity` 以（`chatId`，`messageTimestamp`，`variantIndex`）唯一索引定位版本（`app/src/main/java/com/ai/assistance/operit/data/model/MessageVariantEntity.kt:20`）。
- `applyTo` 把指定版本的内容写回 `ChatMessage` 副本（`app/src/main/java/com/ai/assistance/operit/data/model/MessageVariantEntity.kt:40`）。
- `ChatMessage` 是 `@Serializable` 运行时模型，`sender` 取值为 user 或 ai（`app/src/main/java/com/ai/assistance/operit/data/model/ChatMessage.kt:10`）。
- `ChatHistory` 是 UI 层会话模型（`app/src/main/java/com/ai/assistance/operit/data/model/ChatHistory.kt:9`）。
- Room 声明的 5 个实体中没有独立的工具调用记录表（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:28`）。

### token 用量实体

- 用量记录表 `token_usage_records`（`app/src/main/java/com/ai/assistance/operit/data/model/TokenUsageRecordEntity.kt:9`）。
- `TokenUsageRecordEntity` 记录每次正式推理调用的用量事实（`app/src/main/java/com/ai/assistance/operit/data/model/TokenUsageRecordEntity.kt:16`）。
- 计费价格表 `token_stats_models` 以（`configId`，`provider`，`model`）为复合主键，存用户配置的模型计费价格（`app/src/main/java/com/ai/assistance/operit/data/model/TokenStatsModelEntity.kt:6`）。

### DAO 分层

- `ChatDao` 的 `getAllChats` 返回 `Flow`，按 `pinned` 置顶、`displayOrder` 排序（`app/src/main/java/com/ai/assistance/operit/data/dao/ChatDao.kt:18`）。
- `insertChat` 用 `REPLACE` 冲突策略实现插入或更新（`app/src/main/java/com/ai/assistance/operit/data/dao/ChatDao.kt:33`）。
- `getBranchesByParentId` 查 `parentChatId` 指定的分支会话（`app/src/main/java/com/ai/assistance/operit/data/dao/ChatDao.kt:144`）。
- `getMainChats` 查 `parentChatId IS NULL` 的主会话（`app/src/main/java/com/ai/assistance/operit/data/dao/ChatDao.kt:152`）。
- `insertMessage` 返回插入行的自增 ID（`app/src/main/java/com/ai/assistance/operit/data/dao/MessageDao.kt:139`）。
- `searchChatIdsByContent` 按正文关键词反查会话 ID 列表（`app/src/main/java/com/ai/assistance/operit/data/dao/MessageDao.kt:240`）。
- `copyMessagesToChat` 在会话间复制消息（`app/src/main/java/com/ai/assistance/operit/data/dao/MessageDao.kt:191`）。
- `MessageVariantDao` 是版本表的独立 DAO（`app/src/main/java/com/ai/assistance/operit/data/dao/MessageVariantDao.kt:11`）。
- 正文按 `CONTENT_CHUNK_CHARACTER_COUNT`（65536 字符）分段读取，防止单条大消息撑爆 `CursorWindow`（`app/src/main/java/com/ai/assistance/operit/data/dao/ChatContentDao.kt:11`）。
- 公开读取方法包 `@Transaction`，分段行在事务内拼出完整正文（`app/src/main/java/com/ai/assistance/operit/data/dao/ChatContentDao.kt:276`）。
- `TokenUsageDao` 是抽象类 DAO，提供用量记录插入与聚合查询（`app/src/main/java/com/ai/assistance/operit/data/dao/TokenUsageDao.kt:36`）。
- `aggregateModelsInRange` 按供应商、模型、配置与时间范围聚合用量（`app/src/main/java/com/ai/assistance/operit/data/dao/TokenUsageDao.kt:156`）。

### ObjectBox 侧实体

- `DocumentChunk` 是 ObjectBox `@Entity`（`app/src/main/java/com/ai/assistance/operit/data/model/DocumentChunk.kt:13`）。
- 记忆相关的 `Memory` 实体走 ObjectBox 存储（`app/src/main/java/com/ai/assistance/operit/data/model/Memory.kt:17`）。
- 记忆相关的 `MemoryTag` 实体走 ObjectBox 存储（`app/src/main/java/com/ai/assistance/operit/data/model/Memory.kt:75`）。
- 记忆相关的 `MemoryLink` 实体走 ObjectBox 存储（`app/src/main/java/com/ai/assistance/operit/data/model/Memory.kt:92`）。
- 记忆相关的 `MemoryProperty` 实体走 ObjectBox 存储（`app/src/main/java/com/ai/assistance/operit/data/model/Memory.kt:109`）。
- 以上详见 [[data-memory|记忆系统]] <!-- confidence: INFERRED -->。

## 流程 / 数据流

1. 写消息：`fromChatMessage` 把 `ChatMessage` 转为 `MessageEntity`（`app/src/main/java/com/ai/assistance/operit/data/model/MessageEntity.kt:68`）。
2. 入库：`insertMessage` 写入并返回自增 ID（`app/src/main/java/com/ai/assistance/operit/data/dao/MessageDao.kt:139`）。
3. 读列表：订阅 `getAllChats` 的 `Flow` 拿置顶排序后的会话（`app/src/main/java/com/ai/assistance/operit/data/dao/ChatDao.kt:18`）。
4. 读正文：正文分段读取在 `@Transaction` 方法内完成并拼出完整内容（`app/src/main/java/com/ai/assistance/operit/data/dao/ChatContentDao.kt:276`）。
5. 切版本：`applyTo` 把选中的消息版本写回 `ChatMessage` 副本（`app/src/main/java/com/ai/assistance/operit/data/model/MessageVariantEntity.kt:40`）。
6. 用量回填：版本 20→21 的迁移创建 `token_usage_records` 表（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:270`）。
7. 回填源：把 `messages` 表中 AI 消息的历史 token 写入新表（`app/src/main/java/com/ai/assistance/operit/data/db/AppDatabase.kt:328`）。
8. 用量查询：`aggregateModelsInRange` 按时间范围聚合各模型的用量（`app/src/main/java/com/ai/assistance/operit/data/dao/TokenUsageDao.kt:156`）。

## 来源

- `app/src/main/java/com/ai/assistance/operit/data/model/`（实体类：会话、消息、消息版本、token 用量、ObjectBox 记忆实体）
- `app/src/main/java/com/ai/assistance/operit/data/dao/`（5 个 DAO：聊天、消息、消息版本、正文分段读取、token 用量）
- `app/src/main/java/com/ai/assistance/operit/data/db/`（`AppDatabase` Room 单例与 20 个版本迁移，`ObjectBoxManager` 按 profile 管理 BoxStore）
