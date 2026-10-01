---
title: 权限与 Token 配置界面
module: UI / 权限与 Token
sources: 7
date: 2026-10-01
issue: 118
---

# ui-permission（权限与 Token 配置界面）

> 种子：`app/src/main/java/com/ai/assistance/operit/ui/features/permission/`（2 个 Kotlin 文件）+ `app/src/main/java/com/ai/assistance/operit/ui/features/settings/screens/ToolPermissionSettingsScreen.kt` + `app/src/main/java/com/ai/assistance/operit/ui/features/toolbox/screens/apppermissions/AppPermissionsScreen.kt` + `app/src/main/java/com/ai/assistance/operit/ui/features/token/TokenConfigWebViewScreen.kt`，共 5 个种子文件、约 3,400 行 @ `dbf71916`；路由挂载另引 `app/src/main/java/com/ai/assistance/operit/ui/main/screens/OperitScreens.kt` 与 `app/src/main/java/com/ai/assistance/operit/ui/main/MainActivity.kt`

> 覆盖五块界面：首次启动的权限引导向导（系统权限申请 + AI 能力权限级别选择）、设置里的工具权限总开关（全局主开关 + 按工具逐个允许/禁止）、工具箱里的第三方应用权限管理（查任意 App 的权限并开关）、Token/签到页的 WebView 承载与 URL 配置。

## 概述

Operit 把"权限"拆成三层管：**系统权限**（存储、悬浮窗、电池优化、位置）由首次启动的 PermissionGuideScreen 引导用户去系统设置里打开；**AI 工具权限**（AI 能不能调用某个工具）由 ToolPermissionSettingsScreen 的全局主开关 + 逐工具覆盖控制，默认 ASK（每次询问）；**第三方应用权限**（别的 App 的相机、定位等）由工具箱的 AppPermissionsScreen 通过 shell 命令 `pm grant/revoke` 直接改。

Token 配置界面（TokenConfigWebViewScreen）是一个可配 URL 的 WebView 壳：底部最多 4 个标签，URL 存在 UrlConfigManager 里，点顶栏设置按钮弹 UrlConfigDialog 改配置，改完即时生效。

## AI 速览

- **核心符号清单**：PermissionGuideScreen、PermissionGuideViewModel、PermissionGuideViewModel.Step、PermissionGuideViewModel.UiState、IntroductionPage、WelcomePage、BasicPermissionsPage、PermissionItem、PermissionLevelPage、PermissionLevelItem、ToolPermissionSettingsScreen、PermissionGroup、ToolChip、ToolSelectorDialog、CompactPermissionLevelSelector、handlePermissionChange、AppPermissionsScreen、AppInfo、PermissionInfo、togglePermission、resetAppPermissions、loadInstalledApps、getAppPermissions、extractSectionContent、extractPermissionsFromSection、TokenConfigWebViewScreen、UrlConfigManager、UrlConfigDialog、WebViewConfig、navigateTo。
- **主入口**：MainActivity 引导流程 → PermissionGuideScreen（onComplete 回调）；Screen.TokenConfig → TokenConfigWebViewScreen；Screen.ToolPermissions → ToolPermissionSettingsScreen。
- **数据流向一句话**：用户操作界面 → ViewModel/ToolPermissionSystem/UrlConfigManager 更新状态或落盘 → 界面 collectAsState 重组；第三方 App 权限走 `dumpsys/pm` shell 命令直改系统。

## 核心机制

### 1. 权限引导向导：6 页流程

引导共 6 页：3 页介绍（INTRO_PAGES_COUNT=3，`app/src/main/java/com/ai/assistance/operit/ui/features/permission/screens/PermissionGuideScreen.kt:83`）+ 欢迎页（索引 3，`:84`）+ 基础权限页（索引 4，`:85`）+ 权限级别页（索引 5，`:86`），总页数 TOTAL_PAGES_COUNT=6（`:87`）。

PermissionGuideScreen 是 @OptIn(ExperimentalFoundationApi) 的 @Composable（`:91`），默认用 `viewModel()` 注入 PermissionGuideViewModel（`:92`），完成后调 onComplete 回调。

分页器用 `rememberPagerState(pageCount = { TOTAL_PAGES_COUNT })`（`:100`），HorizontalPager 禁手滑（userScrollEnabled=false，`:221`），只能点底部前后按钮翻页。

启动时 `LaunchedEffect(Unit){ viewModel.checkPermissions(context) }` 初始化四项基础权限状态（`:106`）。

页面切换时 LaunchedEffect 按页索引同步 ViewModel 的步骤：介绍/欢迎页 → Step.WELCOME（`:141`），基础权限页 → Step.BASIC_PERMISSIONS（`:143`），级别页 → Step.PERMISSION_LEVEL（`:145`）。

完成时 `LaunchedEffect(uiState.isCompleted)` 先 delay(500) 展示完成态再调 onComplete()（`:152`）。

下一步按钮逻辑：级别页且已选级别 → savePermissionLevel() 完成（`:447`）；基础权限页但四项未全授予 → 弹警告对话框（`:453`）；否则 animateScrollToPage(+1) 前进（`:457`）。

上一步按钮 `enabled=pagerState.currentPage>0`，首屏禁用（`:403`）。

### 2. 基础权限：四项系统权限的申请

四项基础权限：存储、悬浮窗、电池优化豁免、位置，由 PermissionGuideViewModel.checkPermissions 一次检测（`app/src/main/java/com/ai/assistance/operit/ui/features/permission/viewmodel/PermissionGuideViewModel.kt:44`）。

存储：Android R+ 用 `Environment.isExternalStorageManager()` 判定全部文件访问（`:49`）；R 以下检查 WRITE_EXTERNAL_STORAGE 是否 GRANTED（`:53`）。

悬浮窗：Android M+ 用 `Settings.canDrawOverlays(context)`（`:59`），低于 M 视为已授予（`:61`）。

电池优化豁免：M+ 用 `PowerManager.isIgnoringBatteryOptimizations(packageName)`（`:67`），低于 M 视为已授予（`:69`）。

位置：ACCESS_FINE_LOCATION 或 ACCESS_COARSE_LOCATION 任一 GRANTED 即通过（`:80`）。

四项结果一次写入 UiState，并算出 allBasicPermissionsGranted 为四项逻辑与（`:89`）。

界面申请方式分版本：

- Android 11+ 存储点击直接跳 `Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION` 系统页（`app/src/main/java/com/ai/assistance/operit/ui/features/permission/screens/PermissionGuideScreen.kt:259`），data 带包名直达本应用详情（`:264`）。
- 打不开精准存储设置页时回退 `Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION` 通用页（`app/src/main/java/com/ai/assistance/operit/ui/features/permission/screens/PermissionGuideScreen.kt:274`）。
- Android 10 及以下走运行时权限 launcher 申请读写存储（`app/src/main/java/com/ai/assistance/operit/ui/features/permission/screens/PermissionGuideScreen.kt:291`）。

悬浮窗点击跳 `ACTION_MANAGE_OVERLAY_PERMISSION`（`:304`）；电池优化点击走 `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` 直接请求（`:325`），失败回退 `ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS`（`:340`）；位置点击走 launcher 申请精/粗定位（`:367`）。

位置授权回调里精或粗任一授予即 `viewModel.updateLocationPermission(true)`（`:133`）。

基础权限页的刷新按钮 onRefresh 直接调 `viewModel.checkPermissions(context)` 重检（`:374`）。

### 3. 权限级别：AI 能力档位选择

级别页展示 4 档 AndroidPermissionLevel：STANDARD、ACCESSIBILITY、DEBUGGER、ROOT（由 PermissionLevelPage 渲染，`:818`）。

选档只更新 UiState.selectedPermissionLevel（ViewModel.selectPermissionLevel，`app/src/main/java/com/ai/assistance/operit/ui/features/permission/viewmodel/PermissionGuideViewModel.kt:109`）；下一步按钮启用条件是 `selectedPermissionLevel != null`（`app/src/main/java/com/ai/assistance/operit/ui/features/permission/screens/PermissionGuideScreen.kt:468`）。

确认时 savePermissionLevel()：null 直接打警告日志不保存（`app/src/main/java/com/ai/assistance/operit/ui/features/permission/viewmodel/PermissionGuideViewModel.kt:115`）；非空则在 viewModelScope 里 `androidPermissionPreferences.savePreferredPermissionLevel(level)` 落盘（`:123`），再 `AndroidShellExecutor.clearPreferredPermissionLevelCache()` 清缓存（`:124`），最后置 isCompleted=true。

UiState 是 data class，共 8 字段：currentStep、四项权限布尔、allBasicPermissionsGranted、selectedPermissionLevel、isCompleted（`:156`），currentStep 默认 WELCOME（`:157`）。

### 4. 工具权限总开关：全局 + 逐工具覆盖

ToolPermissionSettingsScreen 是设置里的工具权限界面（`app/src/main/java/com/ai/assistance/operit/ui/features/settings/screens/ToolPermissionSettingsScreen.kt:37`）。

工具列表取自 `toolHandler.getAllToolNames()`，filterNot 掉 `package_proxy`、`proxy`、`search` 三个内部工具（`:44-45`）。

全局主开关初值从 `toolPermissionSystem.masterSwitchFlow.collectAsState(initial = PermissionLevel.ASK)` 取（`:49`），选择后 `saveMasterSwitch(level)` 保存（`:128`）。

单工具覆盖值用 `getToolPermissionOverride(toolName)` 查（`:54`）；界面只展示 ALLOW 与 FORBID 两个分组（`:159`），ASK 是默认兜底不单独分组。

`handlePermissionChange`：重复点同一级别 → `clearToolPermission(toolName)` 清除覆盖回到 ASK（`:71`）；点新级别 → `saveToolPermission(toolName, newLevel)` 保存（`:77`）。

分组卡片 PermissionGroup 按级别配标题/描述/配色（`:179`），工具以 ToolChip 展示，点 X 移除覆盖（`:256`）。

加号按钮弹 ToolSelectorDialog：搜索框用 `contains(searchQuery, ignoreCase=true)` 过滤（`:295`），每行展示工具名与 `getToolDescription(it)` 描述（`:345`）。

CompactPermissionLevelSelector 用 FlowRow 展示 `PermissionLevel.values()` 全级别（`:371`），ALLOW/ASK/FORBID 映射对应 stringResource 文案（`:397`）。

### 5. 第三方应用权限管理：shell 直改

AppPermissionsScreen 是工具箱里的 App 权限管理（`app/src/main/java/com/ai/assistance/operit/ui/features/toolbox/screens/apppermissions/AppPermissionsScreen.kt:63`）。

数据模型：AppInfo(name, packageName, icon, installTime, isSystemApp)（`:44`）；PermissionInfo(name, description, granted, dangerous, group, rawName)（`:52`），rawName 是原始权限名字符串、用于拼 shell 命令。

应用列表由 `loadInstalledApps` 在 Dispatchers.IO 上枚举 `getInstalledApplications` 构建（`:1097`）。

选中应用后 `loadAppPermissions` 调 `getAppPermissions` 解析权限（`:144`）；权限按 `it.group` 分组展示（`:79`）。

`getAppPermissions` 跑两条 shell 命令：`dumpsys package $packageName` 取声明（`:1144`），`dumpsys package $packageName | grep -E "granted=true|:granted=true"` 取已授予（`:1149`）。

段落提取靠 `extractSectionContent(output, sectionHeader)` 截取 requested/install/runtime/grantedPermissions 段（`:1472`），`extractPermissionsFromSection` 从行中提取权限名（`:1503`）。

开关权限直接执行 `pm grant/revoke $packageName ${permission.rawName}`（`:169`），列表内 PermissionItem 的 Switch 同样即时执行（`:729`）。

重置按钮执行 `pm reset-permissions $packageName`（`:196`）。

最终列表按 `sortedWith` 排序：未分组垫底、已授权优先、再按组与名称（`:1461`）。

### 6. Token 配置：可配 URL 的 WebView 壳

TokenConfigWebViewScreen(onNavigateBack) 承载签到/Token 类页面（`app/src/main/java/com/ai/assistance/operit/ui/features/token/TokenConfigWebViewScreen.kt:62`）。

URL 配置由 `UrlConfigManager(context)` 管理（`:66`），界面 `urlConfigFlow.collectAsState(initial=UrlConfig())` 订阅，配置一变即重组（`:69`）。

WebView 由 `WebViewConfig.createWebView(context)` 在 remember 里创建复用（`:77`）；`DisposableEffect(webView)` 绑定 webViewClient 并在 onDispose 里 stopLoading+destroy（`:154`）。

初始加载 `urlConfig.signInUrl`（非空时，`:159`）；底部导航只取 `urlConfig.tabs.take(4)`，最多 4 个标签（`:81`）。

点标签走 `navigateTo(url, index)`：isLoading=true → loadUrl → 更新选中索引（`:91`）。

webViewClient 重写 `shouldOverrideUrlLoading`（`:100`）：`alipays:/alipay:/weixin:/weixins:` 走 ACTION_VIEW Intent 转外部应用（`:114`，加 FLAG_ACTIVITY_NEW_TASK，`:115`）；http/https 留给 WebView。

`onPageFinished` 置 isLoading=false，并按 URL 包含关系修正选中标签（`:136`）。

顶栏设置按钮经 `LocalTopBarActions` 注入（`:169`），只在 `LocalIsCurrentScreen` 为 true 时注入、避免多屏竞争（`:171`、`:175`）。

点设置弹 `UrlConfigDialog(currentConfig=urlConfig)`（`:193`），保存时 `urlConfigManager.saveUrlConfig(newConfig)`（`:197`）。

### 7. 路由挂载

TokenConfigWebViewScreen 挂在 Screen.TokenConfig 的 Content，onNavigateBack=onGoBack（`app/src/main/java/com/ai/assistance/operit/ui/main/screens/OperitScreens.kt:778`）。

ToolPermissionSettingsScreen 挂在 Screen.ToolPermissions 的 Content，navigateBack=onGoBack（`app/src/main/java/com/ai/assistance/operit/ui/main/screens/OperitScreens.kt:814`）。

PermissionGuideScreen 在 MainActivity 引导流程中展示（`app/src/main/java/com/ai/assistance/operit/ui/main/MainActivity.kt:620`）。

## 关键符号

| 符号 | 一句话 |
|---|---|
| PermissionGuideScreen | 6 页引导向导：3 介绍 + 欢迎 + 基础权限 + 权限级别，禁手滑 |
| PermissionGuideViewModel | 检测四项系统权限、选档、落盘权限级别 |
| PermissionGuideViewModel.Step | WELCOME / BASIC_PERMISSIONS / PERMISSION_LEVEL 三步骤枚举 |
| PermissionGuideViewModel.UiState | 8 字段 UI 状态：四项权限 + 全授予与 + 选中级别 + 完成 |
| BasicPermissionsPage | 四项权限列表卡 + 手动刷新按钮 |
| PermissionLevelPage | STANDARD/ACCESSIBILITY/DEBUGGER/ROOT 四档选择 |
| ToolPermissionSettingsScreen | 工具权限总开关：全局主开关 + 逐工具 ALLOW/FORBID 覆盖 |
| handlePermissionChange | 重复点同级清覆盖回 ASK，点新级别保存覆盖 |
| PermissionGroup / ToolChip / ToolSelectorDialog | 分组卡片 / 工具标签 / 带搜索的工具选择弹窗 |
| CompactPermissionLevelSelector | FlowRow 展示全部 PermissionLevel 档位 |
| AppPermissionsScreen | 第三方 App 权限管理：dumpsys 查、pm grant/revoke 改 |
| AppInfo / PermissionInfo | 应用信息 / 权限信息（rawName 供拼 shell 命令） |
| togglePermission / resetAppPermissions | pm grant/revoke 单条切换 / pm reset-permissions 重置 |
| loadInstalledApps / getAppPermissions | IO 线程枚举应用 / 解析 dumpsys 构建权限列表 |
| extractSectionContent / extractPermissionsFromSection | dumpsys 段落截取 / 权限名提取 |
| TokenConfigWebViewScreen | 可配 URL 的 WebView 壳，底部最多 4 标签 |
| UrlConfigManager / UrlConfigDialog | URL 配置读写 / 顶栏设置按钮弹出的配置对话框 |
| WebViewConfig.createWebView | 创建并复用的 WebView 实例 |
| navigateTo | 切标签：isLoading → loadUrl → 更新选中索引 |

## 调用链

1. **首次启动引导**：输入=MainActivity 引导流程 → 处理=PermissionGuideScreen（3 介绍→欢迎→基础权限→级别页，LaunchedEffect 同步 Step）→ 输出=savePermissionLevel 落盘 + clearPreferredPermissionLevelCache + isCompleted → onComplete()。
2. **基础权限申请**：输入=点权限项 → 处理=按 Android 版本分流（11+ 跳系统设置页 / 10- 走运行时 launcher；悬浮窗/电池优化跳对应设置 Intent；位置走 launcher）→ 输出=checkPermissions 重检更新 UiState，全授予后下一步不再弹警告。
3. **工具权限配置**：输入=设置页点工具 → 处理=handlePermissionChange（同级点清覆盖回 ASK，新级别 saveToolPermission；全局开关 saveMasterSwitch）→ 输出=ToolPermissionSystem 落盘，下次工具调用按新级别放行/拦截/询问。
4. **第三方 App 权限修改**：输入=工具箱选 App → 处理=loadAppPermissions（dumpsys 解析）→ 拨 Switch → 输出=`pm grant/revoke <包名> <权限>` shell 执行，成功刷新列表；重置走 `pm reset-permissions`。
5. **Token 页浏览与配置**：输入=打开 Token 页 → 处理=DisposableEffect 加载 signInUrl；点底栏标签 navigateTo 切 URL；点顶栏设置 → 输出=UrlConfigDialog 改 tabs/signInUrl → saveUrlConfig 落盘 → urlConfigFlow 重组即时生效。

## 来源

- 原子事实 124 条（`ui-permission.facts.json`），引用全部实地验真：文件存在、行号在界、断言符号落在引用行 ±5 行内。
- 代码走查 8 条（`ui-permission.quality.json`）：警告 5（pm 命令字符串拼接、调试占位行可拨动执行 pm、URL 未校验 scheme 即 loadUrl、非白名单协议放行 WebView、保存失败仅打日志）、建议 3（底栏硬编码白色、设置返回不自动重检、标签子串匹配易误命中）。
- 注：任务给定的 `settings/screens/PermissionScreen.kt` 与 `settings/screens/TokenConfigScreen.kt` 在源码仓库中不存在（find 全仓库无同名文件）；本页实际覆盖同职能文件 `toolbox/screens/apppermissions/AppPermissionsScreen.kt`（应用权限管理）与 `features/token/TokenConfigWebViewScreen.kt`（Token 配置）。
