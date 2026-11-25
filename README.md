# 老汪的飞牛应用源 · FnDepot 外部应用源 V2

按 [EWEDLCM/FnDepot「外部应用源 V2 编写说明」](https://github.com/EWEDLCM/FnDepot) 编写，收录两个飞牛 fnOS 原生应用。**每个应用只保留最新版本，简介统一为中文，各配 2 张真实软件界面预览图。**

| appname | 应用 | 平台 | 分类 | 当前版本 | 安装包 |
| --- | --- | --- | --- | --- | --- |
| `oesp-fanctl` | OESP风扇助手 | `arm` | 系统工具、硬件驱动 | `1.16` | `arm` |
| `ipsense` | IP 动态感知 | `all` | 系统工具 | `1.1.29` | `all` / `x86` / `arm` |

- **OESP风扇助手**：为 OES Plus（Amlogic S922X）刷 fnOS 打造的 GPIO 直控温控风扇工具，仅 ARM64 / OES Plus 可用，因此 `platform` 限定为 `arm`，x86 设备上客户端会自动隐藏。
- **IP 动态感知**：6 类访问与扫描日志的可视化观测应用，只观测、不封禁、不改防火墙。上游同时发布 `all`、`x86`、`arm` 三个包，正好对应 V2 的架构选择顺序 `packages.[当前架构] -> packages.all`：x86 / ARM 设备优先取专用包，`all` 作为通用回退。

> 外部源由用户自行添加，仅在本地客户端生效；FnDepot 不对外部源的应用代码、安装包安全性或运行稳定性做审核、担保或背书。

## 添加源

> ⚠️ V2 规范需要 **FnDepot 客户端 > 0.0.7**。飞牛已启用 httponly，旧版客户端无法继续使用，请先升级客户端。

在 FnDepot 客户端里添加以下任意一种地址：

```
# 方式一：GitHub 仓库根地址（客户端会读取仓库根目录的 fnpack.json）
https://github.com/wangbujiangwude/fndepot-source

# 方式二：JSON 直链
https://raw.githubusercontent.com/wangbujiangwude/fndepot-source/main/fnpack.json
```

仓库根地址模式要求根目录**必须**存在大小写完全一致的 `fnpack.json`；若改用其它文件名或子目录，请给用户提供 JSON 直链，而不是仓库根地址。

> 修改源后客户端可能仍显示旧缓存，重新添加源或刷新外部源即可看到中文简介与预览图。

## 目录结构

V2 不强制目录布局，客户端只按 `fnpack.json` 里的 URL 定位资源。本源采用「单文件模式 + 仓库内图标/预览图 + 上游 Releases 直链」：

```
fndepot-source/
├── fnpack.json                      # V2 源索引（单文件模式，每应用仅最新版本）
├── README.md                        # 本说明
├── assets/
│   ├── oesp-fanctl.png              # 图标
│   ├── ipsense.png                  # 图标
│   └── preview/                     # 应用预览图（每个应用 2 张）
│       ├── oesp-fanctl-1.png
│       ├── oesp-fanctl-2.png
│       ├── ipsense-1.png
│       └── ipsense-2.png
└── scripts/
    ├── build_source.py              # 从 GitHub Releases 自动重建 fnpack.json
    ├── verify_source.py             # 发布前校验
    └── official-v2-sample.json      # FnDepot 官方 V2 源样例快照，供字段对照
```

- **图标 / 预览图**用相对 URL（相对主 JSON 所在地址解析），随源仓库一起发布；
- **FPK 安装包**用绝对 URL 指向上游两个项目的 GitHub Releases，不复制 FPK 到本仓库；
- **`readme_url` / `bug_report_url`** 指向上游项目的 README 与 Issues。

## 中文简介与预览图

**简介**：`display_name`、`desc` 全部为中文基础字段，`desc` 支持 HTML（`<br>` 分段、`<b>` 强调，客户端会清理危险内容）。IP 动态感知简介末尾按要求加了一行 `企鹅群：1132993836`。

**为什么不给 `i18n`**：V2 的回退顺序是「精确语言 → 同语系候选 → `en-US` → `zh-CN` → 基础字段」，`en-US` 排在基础字段之前。此前源里提供了 `en-US` 英文文案，导致中文系统的客户端也命中英文，应用名和简介显示成英文。现在移除全部 `i18n` 分支，任何语言环境最终都回退到中文基础字段；基础字段仍按规范完整填写。

**预览图**（`preview_urls`，每个应用 2 张，均为软件真实界面）：

| 文件 | 内容 | 来源 |
| --- | --- | --- |
| `oesp-fanctl-1.png` | 仪表盘总览（状态卡、12 小时温度曲线、温控阈值设置） | 上游 `docs/images/04-dashboard.png` |
| `oesp-fanctl-2.png` | 运行中界面（另一状态，DDR / 硬盘温度） | 1.16 推文 `images/04-ui.png` |
| `ipsense-1.png` | 顶部四张统计卡 + 境外来源全球地图 | 上游离线预览页渲染 |
| `ipsense-2.png` | 访问统计与排名、五张分析卡、实时访问事件与趋势图 | 上游离线预览页渲染 |

IP 动态感知上游仓库里没有现成界面截图，因此用仓库自带的 `tools/make_preview.py` 把**真实前端首页（`index.html` + `style.css` + `app.js`）与模拟数据**打包成离线预览页，再由本机 Chrome 无头渲染截图、按自然区块边界裁切得到。客户端最多读取前 8 张预览图，单张建议 < 2MB；本源 4 张合计约 1.9MB。

## 字段取值依据

| 字段 | 取值 | 依据 |
| --- | --- | --- |
| `schema_version` | `"2"`（字符串） | V2 规范，不能写成 `2` 或 `"2.0"` |
| `source_info.author` | 老汪不讲武德 | 源维护者；与 `maintainer` 恰为同一主体 |
| `appname` | `oesp-fanctl` / `ipsense` | 与两个 FPK `manifest` 的 `appname` 完全一致、保留大小写 |
| `platform` | `["arm"]` / `["all"]` | 取自两个 FPK `manifest` 的 `platform` |
| `categories` | 固定九个分类内，最多 2 个 | 主分类写在数组第一项 |
| `preview_urls` | 每个应用 2 个相对 URL | V2 可选的 URL 字符串数组，最多读取前 8 张 |
| `run_as` | `"package"` | 与 FnDepot 官方源全部应用写法一致（FPK 内部的 `config/privilege` run-as 为 root，属包内运行身份，两者不冲突） |
| `install_type` | `"root"` | 系统空间；与官方源 `fntermx` 等原生 FPK 应用一致 |
| `is_docker` | `false` | 两者都是 fnOS 原生 FPK，非 Docker 应用 |
| `service_port` | `""` | 都通过飞牛统一网关 `/app/<appname>` 访问，无独立服务端口（`ipsense` manifest `checkport = false`） |
| `os_min_version` | ipsense `1.1.8` | 取自 `ipsense` 的 FPK manifest；`oesp-fanctl` 未声明，留空表示不限制 |

如客户端实际安装行为与上述判断不符，只需改 `scripts/build_source.py` 里的 `APPS` 常量后重新生成。

## 版本号、哈希与下载地址

这三项最容易手抄出错，因此全部由脚本从上游自动生成，不手工维护：

- **版本号**取自 FPK 文件名（`oesp-fanctl_1.16_arm.fpk` → `1.16`），保证与 FPK 内部 `manifest` 的 `version` 一致；`v1.16.0` 这类 git tag 仅用于定位 Release，不写进源。
- **`sha256`** 取 GitHub Release asset 的 `digest`，**`size`** 取 `size`（Bytes，非负整数）。存在 sha256 时客户端会强制校验。
- **`download_url`** 用 `browser_download_url` 绝对直链。
- **`updated_at`** 由 Release 的 `published_at` 转成 `+08:00` 的 ISO 8601；**`changelog`** 取 Release 标题并去掉重复的版本号前缀。
- 非 FPK 附件（如 `ipsense-agent-bridge.zip`）会被自动跳过。

`ipsense` 的 `ipsense-agent-bridge` skill 包与 FPK 分开安装，不属于本源的安装包范畴，用户需从对应 Release 自行下载。

## 更新流程

上游项目发新版后：

```bash
# 1. 重建源（默认只保留每个应用的最新版本，历史版本不写入）
python scripts/build_source.py

# 需要全部历史版本时（本源默认不用）
python scripts/build_source.py --all-versions

# 2. 校验
python scripts/verify_source.py
python scripts/verify_source.py --check-manifest   # 联网核对 appname / 最新版本
python scripts/verify_source.py --check-urls       # 联网 HEAD 检查所有绝对 URL

# 3. 提交并推送（GitHub 仓库模式会自动生效）
git add fnpack.json && git commit -m "chore: 同步上游最新版本" && git push
```

若同时替换了预览图，把 `assets/preview/` 一起 `git add`。如果 GitHub API 触发限流，可设置 `GITHUB_TOKEN` 环境变量后再运行生成脚本。

**发布纪律**（V2 规范第 13 节）：

- 已发布的「版本号 + 架构」FPK 视为不可变，内容变更必须发新版本或新地址，不要静默替换同版本 FPK。
- 移除版本 / 应用时，从 `releases` / `apps` 里显式删除对应键；不要靠返回空文件或格式错误来"下架"，那会触发客户端缓存保留。
- 不要手写 `source_info.id`，该字段不参与客户端的身份识别与去重。

## 校验清单

`verify_source.py` 覆盖官方第 12 节的检查项：严格 JSON、`schema_version`、`source_info`、appname 合法性、必填元数据、固定分类与平台枚举、`run_as` / `install_type` / `is_docker` 类型、URL 协议与相对资源是否存在、`preview_urls` 数量、`packages` 架构键、`download_url` 必填、`sha256` / `size` 格式、版本数与 i18n 字段层级，并可选联网核对 FPK manifest 与 URL 可达性。

手工复核命令（Git Bash / Linux）：

```bash
jq empty fnpack.json
python scripts/verify_source.py --check-manifest --check-urls
```

## 客户端限制备忘

主源 JSON ≤ 约 2MB · 单个源 ≤ 5000 应用 · 单应用 ≤ 100 版本 · 单应用最多读取 8 张预览图 · 图标建议 < 500KB · 预览图单张尽量 < 2MB · 所有 URL 只允许 `http` / `https`（相对 URL 亦可），不要放用户名、密码或长期令牌。

运行时语言以 fnOS 环境变量 `TRIM_SYS_LANGUAGE` 为准，不以浏览器 Cookie 或 `Accept-Language` 为准；本源不提供 `i18n`，所有语言环境最终回退到中文基础字段。
