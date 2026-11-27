# 老汪的飞牛应用源 · FnDepot 外部应用源 V2

按 [EWEDLCM/FnDepot「外部应用源 V2 编写说明」](https://github.com/EWEDLCM/FnDepot) 编写，收录两个飞牛 fnOS 原生应用。**保留全部历史版本，简介统一为中文，各配 2 张真实软件界面预览图。**

| appname | 应用 | 平台 | 分类 | 版本范围 | 安装包 |
| --- | --- | --- | --- | --- | --- |
| `oesp-fanctl` | OESP风扇助手 | `arm` | 系统工具、硬件驱动 | `1.15` ~ `1.16`（2 版） | 2 个（`arm`） |
| `ipsense` | IP 动态感知 | `all` | 系统工具 | `1.1.14` ~ `2.0.0`（17 版） | 51 个（`all` / `x86` / `arm`） |

合计 53 个安装包，`fnpack.json` 约 22KB。

- **OESP风扇助手**：为 OES Plus（Amlogic S922X）刷 fnOS 打造的 GPIO 直控温控风扇工具，仅 ARM64 / OES Plus 可用，因此 `platform` 限定为 `arm`，x86 设备上客户端会自动隐藏。
- **IP 动态感知**：6 类访问与扫描日志的可视化观测应用，只观测、不封禁、不改防火墙。上游同时发布 `all`、`x86`、`arm` 三个包，正好对应 V2 的架构选择顺序 `packages.[当前架构] -> packages.all`：x86 / ARM 设备优先取专用包，`all` 作为通用回退。

> 外部源由用户自行添加，仅在本地客户端生效；FnDepot 不对外部源的应用代码、安装包安全性或运行稳定性做审核、担保或背书。

## 添加源

> ⚠️ V2 规范需要 **FnDepot 客户端 > 0.0.7**。飞牛已启用 httponly，旧版客户端无法继续使用，请先升级客户端。

在 FnDepot 客户端里添加以下任意一种地址：

```
# 方式一（推荐）：JSON 直链 —— 直接读 raw，源改完立刻生效
https://raw.githubusercontent.com/wangbujiangwude/fndepot-source/main/fnpack.json

# 方式二：GitHub 仓库根地址 —— 短、好记，但可能受 CDN 缓存延迟影响
https://github.com/wangbujiangwude/fndepot-source
```

- **直链模式**不强制文件名，内容符合 V1 / V2 结构即可（客户端按内容识别格式，不按文件名）。
- **仓库根地址模式**有固定要求：根目录**必须**存在大小写完全一致的 `fnpack.json`；客户端优先使用仓库默认分支，GitHub API 不可用时兼容尝试 `main`、`master`；不会探测 `fndepot.json` 等其它索引文件名。若改用其它文件名或子目录，请给用户提供 JSON 直链，而不是仓库根地址。

> 修改源后客户端可能仍显示旧缓存，**删除该源重新添加**或刷新外部源，即可看到全部历史版本、中文简介与预览图。

### 为什么仓库根地址会「看不到历史版本」

GitHub 仓库文件常被 jsDelivr 这类 CDN 加速，而 CDN 对 `@main` 分支的缓存很长（响应头 `max-age=604800`、`s-maxage=43200`）。本源 2026-11-26 从「仅最新版本」恢复为「全部历史版本」后实测：

| 通道 | 返回内容 |
| --- | --- |
| `raw.githubusercontent.com/.../fnpack.json`（直链） | 22306B / 17 版 / 最新 2.0.0 ✅ |
| `github.com/.../raw/main/fnpack.json` | 22306B / 17 版 / 最新 2.0.0 ✅ |
| `cdn.jsdelivr.net/gh/...@main/fnpack.json`（purge 前） | **4427B / 只有 1.1.29 一个版本** ❌ |

CDN 节点还缓存着上一版精简源文件（`Age` 约 8.8 小时），所以仓库根地址模式短暂地看不到历史版本，而直链读 raw 是最新的。**已内置自动刷新**：

- `.github/workflows/purge-cdn.yml`：每次 `fnpack.json` 或 `assets/**` 推送到 `main` 时，自动调用 jsDelivr purge API 清除缓存；也支持在 Actions 页面手动触发（`workflow_dispatch`）。
- `scripts/purge_cdn.py`：本地手动刷新，并核对 CDN 内容与本地 `fnpack.json` 是否一致。

```bash
python scripts/purge_cdn.py            # 仅刷新缓存
python scripts/purge_cdn.py --check   # 刷新并核对两个 CDN 节点
```

> 注意 CDN 刷新解决的是「服务器侧旧内容」；客户端自身还有短时缓存（`ETag` / `Last-Modified` 条件请求），必要时仍需删除源重新添加。

## 目录结构

V2 不强制目录布局，客户端只按 `fnpack.json` 里的 URL 定位资源。本源采用「单文件模式 + 仓库内图标/预览图 + 上游 Releases 直链」：

```
fndepot-source/
├── fnpack.json                      # V2 源索引（单文件模式，含全部历史版本）
├── README.md                        # 本说明
├── .github/workflows/
│   └── purge-cdn.yml                # push 后自动刷新 jsDelivr CDN 缓存
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
    ├── purge_cdn.py                 # 手动刷新 CDN 缓存并核对一致性
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
# 1. 重建源（默认保留全部历史版本，新版本追加到 releases）
python scripts/build_source.py

# 只想临时生成「仅最新版本」的源时（注意：会覆盖线上 fnpack.json）
python scripts/build_source.py --latest-only

# 2. 校验
python scripts/verify_source.py
python scripts/verify_source.py --check-manifest   # 联网核对 appname / 最新版本
python scripts/verify_source.py --check-urls       # 联网 HEAD 检查所有绝对 URL

# 3. 提交并推送（GitHub 仓库模式会自动生效）
git add fnpack.json && git commit -m "chore: 同步上游全部版本" && git push

# 4. 刷新 CDN 缓存（仓库根地址模式需要）
#    .github/workflows/purge-cdn.yml 会在 push 时自动执行；本地也可手动：
python scripts/purge_cdn.py --check
```

若同时替换了预览图，把 `assets/preview/` 一起 `git add`。如果 GitHub API 触发限流，可设置 `GITHUB_TOKEN` 环境变量后再运行生成脚本。

**发布纪律**（V2 规范第 13 节）：

- 已发布的「版本号 + 架构」FPK 视为不可变，内容变更必须发新版本或新地址，不要静默替换同版本 FPK。
- 移除版本 / 应用时，从 `releases` / `apps` 里显式删除对应键；不要靠返回空文件或格式错误来"下架"，那会触发客户端缓存保留。
- 不要手写 `source_info.id`，该字段不参与客户端的身份识别与去重。

## 校验清单

`verify_source.py` 覆盖官方第 12 节的检查项：严格 JSON、`schema_version`、`source_info`、appname 合法性、必填元数据、固定分类与平台枚举、`run_as` / `install_type` / `is_docker` 类型、URL 协议与相对资源是否存在、`preview_urls` 数量、`packages` 架构键、`download_url` 必填、`sha256` / `size` 格式、版本数与 i18n 字段层级，并可选联网核对 FPK manifest 与 URL 可达性。

`--check-urls` 的兜底：本机代理的 `github.com` 隧道偶发 `502` 时，HEAD 失败的下载地址会再用 GitHub API 的 Release 资产清单核对 URL / `size` / `sha256`，页面类 URL 则核对仓库存在性；一致即视为有效，并在输出里标注「API 资产核对一致」，避免把网络抖动误判成源写错。

手工复核命令（Git Bash / Linux）：

```bash
jq empty fnpack.json
python scripts/verify_source.py --check-manifest --check-urls
```

## 常见问题：同一个源，两个界面「简介」不一样

2026-11-27 实测：两个客户端添加同一个源，IP 动态感知的「简介」一个是简洁中文简介（含 `企鹅群：1132993836`）+ 2 张预览图，另一个却是「2.0.0 大版本更新：…」长篇更新日志 + 4 张图。**源本身没有问题**：本地 `fnpack.json` 与 `raw.githubusercontent.com`、`cdn.jsdelivr.net` 逐字节一致（22306B），4 次提交里 `desc` 一直是 235 字简洁中文、`preview_urls` 一直是 2 张，从未出现长文或 4 张图。差异来自两边读的不是同一份数据。

| 界面 | 实际读取 | 显示结果 |
| --- | --- | --- |
| 外部源详情页 | `fnpack.json` → `apps.ipsense.desc` | 简洁中文简介 + `preview_urls` 的 2 张图 |
| 已安装应用详情页 / 网页端 | 已安装 FPK 内 `manifest` 的 `changelog`（2271 字累积更新日志），或本地旧缓存 | 长篇「2.0.0 大版本更新：…」+ 非源内的预览图 |

V2 规范里 `desc` 才是「应用简介」，`changelog` 只是「版本更新说明」，`readme_url` 是独立的 README 分页入口，三者不是同一个字段。已安装态展示 FPK 内 `manifest` 的内容而不读源的 `desc`，所以会出现「同一个源、两种介绍」。已从线上 2.0.0 FPK 用 HTTP Range 增量解压验证：包内 `desc` 与源完全一致，`changelog` 正是那段长文。

按顺序排查并统一：

1. **删源重加**：客户端对源和详情用 `ETag` / `Last-Modified` 短缓存，同步失败还会保留上一次有效缓存。两个客户端都删除该源再重新添加。
2. **统一用 JSON 直链**：`https://raw.githubusercontent.com/wangbujiangwude/fndepot-source/main/fnpack.json`。仓库根地址走 jsDelivr CDN，`@main` 分支缓存很长；官方 `valid_sources.txt` 收录的是本源的仓库根地址，实测 `fastly.jsdelivr.net` 在多次 purge 后仍返回旧快照（旧文件恰好同为 22306B，只差 2.0.0 三个包的 `size` / `sha256`）。
3. **卸载重装**：显示长文的那台，把 IP 动态感知卸载后重新安装 2.0.0，让它读新 FPK 的 `manifest`。
4. **核对版本与哈希**：两边都应是 2.0.0 / 4.37 MB，`size` 与 `sha256` 与 `fnpack.json` 一致。

> 根因复盘：为把简介改回简洁版，曾在 2.0.0 版本号不变的情况下**原地替换了三个 FPK 并改写 `sha256` / `size`**，这违反了 V2「已发布 FPK 视为不可变、不要静默替换同版本 FPK」的发布纪律。已经下载 / 安装过旧 2.0.0 的客户端本地仍是旧包，于是同一源、不同安装时间，展示必然分叉。以后内容变更一律发新版本号（如 2.0.1）+ 新 `download_url` / `size` / `sha256`。

## 客户端限制备忘

主源 JSON ≤ 约 2MB · 单个源 ≤ 5000 应用 · 单应用 ≤ 100 版本 · 单应用最多读取 8 张预览图 · 图标建议 < 500KB · 预览图单张尽量 < 2MB · 所有 URL 只允许 `http` / `https`（相对 URL 亦可），不要放用户名、密码或长期令牌。

源和详情请求使用短时缓存、`ETag` 与 `Last-Modified` 条件请求；同步失败时客户端会保留上一次有效缓存，不会用空结果覆盖。运行时语言以 fnOS 环境变量 `TRIM_SYS_LANGUAGE` 为准，不以浏览器 Cookie 或 `Accept-Language` 为准；本源不提供 `i18n`，所有语言环境最终回退到中文基础字段。
