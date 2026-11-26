#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 GitHub Releases 自动生成 FnDepot 外部应用源 V2 的 fnpack.json。

数据源：
  - wangbujiangwude/oesp-fanctl   （OESP 风扇助手，仅 arm 包）
  - wangbujiangwude/ipsense-fnos  （IP 动态感知，all / x86 / arm 三包）

版本号取自 FPK 文件名（与 FPK manifest 内的 version 保持一致），
sha256 / size 直接取 GitHub Release asset 的 digest / size，不手工填写。

约定（2026-11-25 起）：
  - 简介只写中文基础字段，不提供 i18n.en-US 覆盖。V2 回退顺序里 en-US
    排在基础字段之前，只要存在 en-US，中文环境下客户端也会显示英文。
  - 默认保留全部历史版本；只要最新版本用 --latest-only。
  - 每个应用固定配 2 张预览图（真实软件界面），放在 assets/preview/。

用法：
  python scripts/build_source.py                  # 生成全部历史版本（默认）
  python scripts/build_source.py --latest-only   # 每个应用只保留最新版本
  python scripts/build_source.py --dry-run       # 只打印统计，不写文件
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fnpack.json"

OWNER = "wangbujiangwude"
API = "https://api.github.com/repos/{owner}/{repo}/releases?per_page=100"

SOURCE_INFO = {
    "name": "老汪的飞牛应用源",
    "author": "老汪不讲武德",
    "homepage": "https://github.com/wangbujiangwude",
    "description": "OESP 风扇助手与 IP 动态感知的 FnDepot 外部应用源（V2）",
    # 不提供 i18n：让所有语言环境都回退到中文基础字段
}

# 应用静态元数据。releases 由脚本从 GitHub Releases 自动生成。
APPS = {
    "oesp-fanctl": {
        "repo": "oesp-fanctl",
        "display_name": "OESP风扇助手",
        "desc": (
            "专为 OES Plus（Amlogic S922X）刷飞牛 fnOS 打造的智能温控风扇管理工具："
            "GPIO 直控、安装即用，自动从设备树读取风扇引脚并接管系统自带风扇服务。<br><br>"
            "支持自动温控 / 常开 / 常关三种模式、启停延迟与温度中位数滤波、"
            "硬盘温度监控开关、12 小时温度曲线与网页在线调参。<br><br>"
            "⚠️ 仅适用于 OES Plus（ARM64），其它机型请勿安装。"
        ),
        "platform": ["arm"],
        "categories": ["系统工具", "硬件驱动"],
        "icon_url": "./assets/oesp-fanctl.png",
        "preview_urls": [
            "./assets/preview/oesp-fanctl-1.png",
            "./assets/preview/oesp-fanctl-2.png",
        ],
        "readme_url": f"https://raw.githubusercontent.com/{OWNER}/oesp-fanctl/main/README.md",
        "bug_report_url": f"https://github.com/{OWNER}/oesp-fanctl/issues",
        "maintainer": "老汪不讲武德",
        "maintainer_url": f"https://github.com/{OWNER}",
        "run_as": "package",
        "install_type": "root",
        "is_docker": False,
        "service_port": "",
        # 不提供 i18n.en-US，避免中文环境下客户端命中英文文案
    },
    "ipsense": {
        "repo": "ipsense-fnos",
        "display_name": "IP 动态感知",
        "desc": (
            "把飞牛 NAS 的 6 类访问与扫描日志收成一张能点的地图：本机 SSH、Web、"
            "fnOS 登录审计、路由器 syslog、端口敲门与敲门网关日志。<br><br>"
            "提供境内 / 境外双地图、IP 来源画像（4 票归属裁决）、五张分析卡，"
            "以及可直接交给 AI 的 Markdown 汇总日志；x86 / ARM64 通用。<br><br>"
            "<b>只观测、不封禁、不改防火墙、不自动处置</b>；处置完全交给外部 agent 的「提交单」。<br>"
            "企鹅群：1132993836"
        ),
        "platform": ["all"],
        "categories": ["系统工具"],
        "icon_url": "./assets/ipsense.png",
        "preview_urls": [
            "./assets/preview/ipsense-1.png",
            "./assets/preview/ipsense-2.png",
        ],
        "readme_url": f"https://raw.githubusercontent.com/{OWNER}/ipsense-fnos/main/README.md",
        "bug_report_url": f"https://github.com/{OWNER}/ipsense-fnos/issues",
        "maintainer": "老汪不讲武德",
        "maintainer_url": f"https://github.com/{OWNER}",
        "run_as": "package",
        "install_type": "root",
        "is_docker": False,
        "service_port": "",
        # FPK manifest: os_min_version = 1.1.8
        "os_min_version": "1.1.8",
        # 不提供 i18n.en-US，避免中文环境下客户端命中英文文案
    },
}

FPK_RE = re.compile(r"^.+?_(\d+(?:\.\d+)*)_(all|x86|arm)\.fpk$", re.IGNORECASE)
VALID_ARCH = {"all", "x86", "arm"}


def fetch_releases(repo: str) -> list[dict]:
    url = API.format(owner=OWNER, repo=repo)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "fndepot-source-builder/1.0",
            "Accept": "application/vnd.github+json",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if not isinstance(data, list):
        raise RuntimeError(f"{repo}: GitHub API 未返回列表：{str(data)[:200]}")
    return data


def to_cst(iso_utc: str) -> str:
    """GitHub 的 UTC 时间转 ISO 8601 +08:00。"""
    if not iso_utc:
        return dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds")
    t = dt.datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    return t.astimezone(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds")


def clean_changelog(name: str, body: str, version: str) -> str:
    text = (name or "").strip()
    if not text:
        for line in (body or "").splitlines():
            line = line.strip().lstrip("#").strip()
            if line:
                text = line
                break
    # 去掉标题开头重复的版本号，例如 "ipsense 1.1.29 · "
    text = re.sub(r"^[\w\-\s\.]*?" + re.escape(version) + r"\s*[·\-:：]?\s*", "", text).strip()
    text = re.sub(r"^OESP 风扇助手\s*[\d\.]+\s*[·\-:：]?\s*", "", text).strip()
    if len(text) > 160:
        text = text[:157].rstrip() + "…"
    return text or f"版本 {version}"


def version_key(v: str):
    parts = []
    for p in v.split("."):
        parts.append((0, int(p)) if p.isdigit() else (1, p))
    return tuple(parts)


def build_releases(repo: str, latest_only: bool) -> dict:
    releases = fetch_releases(repo)
    out: dict[str, dict] = {}
    skipped = []

    for rel in releases:
        if rel.get("draft"):
            continue
        pkgs: dict[str, dict] = {}
        version = None

        for asset in rel.get("assets", []):
            name = asset.get("name", "")
            m = FPK_RE.match(name)
            if not m:
                continue  # 跳过 ipsense-agent-bridge.zip 等非 FPK 附件
            version, arch = m.group(1), m.group(2).lower()
            if arch not in VALID_ARCH:
                continue
            entry = {
                "download_url": asset["browser_download_url"],
                "size": int(asset["size"]),
            }
            digest = asset.get("digest") or ""
            if digest.startswith("sha256:") and len(digest) == 71:
                entry["sha256"] = digest[7:]
            pkgs[arch] = entry

        if not pkgs or not version:
            skipped.append(rel.get("tag_name", "?") + " (无 FPK 资产)")
            continue

        node = {
            "changelog": clean_changelog(rel.get("name", ""), rel.get("body", ""), version),
            "updated_at": to_cst(rel.get("published_at") or rel.get("created_at")),
            "packages": {k: pkgs[k] for k in ("all", "x86", "arm") if k in pkgs},
        }
        os_min = APPS[_app_key_by_repo(repo)].get("os_min_version")
        if os_min:
            node["os_min_version"] = os_min
        # 版本号 + 架构文件视为不可变；同一版本被重复发布时保留信息更全的一条
        if version not in out or len(pkgs) > len(out[version]["packages"]):
            out[version] = node

    if skipped:
        print(f"  [{repo}] 跳过的 release: {', '.join(skipped)}", file=sys.stderr)

    if latest_only and out:
        newest = sorted(out, key=version_key)[-1]
        out = {newest: out[newest]}

    return {v: out[v] for v in sorted(out, key=version_key)}


def _app_key_by_repo(repo: str) -> str:
    for k, v in APPS.items():
        if v["repo"] == repo:
            return k
    raise KeyError(repo)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latest-only", action="store_true", help="每个应用只保留最新版本（默认保留全部历史版本）")
    ap.add_argument("--dry-run", action="store_true", help="只打印统计，不写 fnpack.json")
    args = ap.parse_args()

    apps_out = {}
    for key, meta in APPS.items():
        print(f"拉取 {OWNER}/{meta['repo']} 的 Releases …")
        rels = build_releases(meta["repo"], args.latest_only)
        if not rels:
            print(f"  ✗ {key}: 没有可用版本，终止", file=sys.stderr)
            return 1
        app = {k: v for k, v in meta.items() if k != "repo"}
        app["releases"] = rels
        apps_out[key] = app
        pkg_count = sum(len(r["packages"]) for r in rels.values())
        print(f"  ✓ {key}: {len(rels)} 个版本 / {pkg_count} 个安装包，最新 {sorted(rels, key=version_key)[-1]}")

    doc = {"schema_version": "2", "source_info": SOURCE_INFO, "apps": apps_out}

    if args.dry_run:
        print("\n--dry-run，未写文件。")
        return 0

    # 用 write_bytes 固定 UTF-8 + LF，避免 Windows 上被转成 CRLF，
    # 保证 GitHub 与本地的字节数、以及 sha256/size 口径一致。
    OUT.write_bytes((json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"\n已生成 {OUT} ({OUT.stat().st_size} 字节)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
