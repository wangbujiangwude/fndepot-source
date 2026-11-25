#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FnDepot 外部应用源 V2 发布前校验（对应官方 README 第 12 节检查清单）。

用法：
  python scripts/verify_source.py                    # 本地静态校验
  python scripts/verify_source.py --check-manifest  # 额外联网核对 FPK manifest 的 appname/version
  python scripts/verify_source.py --check-urls      # 额外 HEAD 检查所有绝对 URL
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "fnpack.json"

CATEGORIES = {
    "影音娱乐", "系统工具", "编程开发", "AI赋能", "生活服务",
    "智能智控", "教育学习", "游戏地带", "硬件驱动",
}
PLATFORMS = {"all", "x86", "arm"}
ARCHS = {"all", "x86", "arm"}
APPNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
BAD_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:(//)?")

errors: list[str] = []
warns: list[str] = []
infos: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warns.append(msg)


def check_url(u: str, where: str, *, must_be_local: bool = False) -> None:
    if not isinstance(u, str) or not u:
        err(f"{where}: URL 为空或不是字符串")
        return
    if u.startswith(("http://", "https://")):
        if "@" in u.split("//", 1)[-1].split("/", 1)[0]:
            err(f"{where}: URL 中不得包含用户名/密码/令牌")
        return
    m = BAD_URL_RE.match(u)
    if m and not u.startswith(("./", "../", "/")):
        scheme = u.split(":", 1)[0]
        if scheme in ("file", "ftp", "data", "javascript"):
            err(f"{where}: 不允许的协议 {scheme}")
    # 相对 URL：校验本地文件存在
    if not u.startswith(("http://", "https://")):
        p = (ROOT / u).resolve()
        if not p.exists():
            err(f"{where}: 相对 URL 指向的本地文件不存在 -> {u}")
        elif p.stat().st_size == 0:
            err(f"{where}: 本地资源文件为空 -> {u}")


def fetch_text(url: str, *, retries: int = 1) -> tuple[str, int]:
    """urllib 为主（raw.githubusercontent.com 偶发超时），curl 兜底。"""
    import subprocess
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "fndepot-verify/1.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                return r.read().decode("utf-8", "replace"), r.status
        except Exception:
            continue
    try:
        p = subprocess.run(
            ["curl", "-sS", "--max-time", "25", url],
            capture_output=True,
        )
        if p.returncode == 0:
            out = p.stdout.decode("utf-8", "replace")
            if out and not out.startswith("404"):
                return out, 200
    except Exception:
        pass
    return "", 0


def check_manifest(appname: str, repo: str, latest: str) -> None:
    import base64
    text = ""
    for path in ("manifest", "src/manifest"):
        # 优先走 GitHub Contents API（api.github.com 比 raw 稳定）
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/wangbujiangwude/{repo}/contents/{path}",
                headers={
                    "User-Agent": "fndepot-verify/1.0",
                    "Accept": "application/vnd.github+json",
                },
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                obj = json.load(r)
            text = base64.b64decode(obj["content"]).decode("utf-8", "replace")
            if text:
                break
        except Exception:
            pass
        # raw + curl 兜底
        text, status = fetch_text(
            f"https://raw.githubusercontent.com/wangbujiangwude/{repo}/main/{path}"
        )
        if status == 200 and text:
            break
        text = ""
    if not text:
        warn(f"{appname}: 未能读取上游 FPK manifest，跳过一致性核对")
        return
    kv = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            kv[k.strip()] = v.strip()
    if kv.get("appname") != appname:
        err(f"{appname}: 上游 manifest 的 appname={kv.get('appname')!r} 与源键名不一致")
    if kv.get("version") and kv["version"] != latest:
        warn(f"{appname}: 上游 manifest version={kv['version']}，源最新版本={latest}（可能上游已发新版）")
    infos.append(f"{appname}: 上游 manifest appname={kv.get('appname')} version={kv.get('version')} platform={kv.get('platform')}")


def head_url(u: str, *, retries: int = 2) -> tuple[str, str]:
    req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "fndepot-verify/1.0"})
    last = ""
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return u, f"HTTP {r.status} ({r.headers.get('Content-Length', '?')} bytes)"
        except Exception as e:
            last = f"FAIL {type(e).__name__}: {str(e)[:80]}"
    return u, last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-manifest", action="store_true")
    ap.add_argument("--check-urls", action="store_true")
    args = ap.parse_args()

    try:
        raw = SRC.read_text(encoding="utf-8")
        d = json.loads(raw)  # 严格 JSON：注释 / 尾逗号会直接报错
    except Exception as e:
        print(f"✗ fnpack.json 不是严格 JSON：{e}")
        return 1
    infos.append(f"fnpack.json 严格 JSON 解析通过，{len(raw.encode('utf-8'))} 字节（上限约 2MB）")

    # 顶层
    if d.get("schema_version") != "2" or not isinstance(d.get("schema_version"), str):
        err("schema_version 必须是字符串 \"2\"")
    si = d.get("source_info")
    if not isinstance(si, dict):
        err("source_info 缺失或类型错误")
        si = {}
    for k in ("name", "author"):
        if not isinstance(si.get(k), str) or not si[k].strip():
            err(f"source_info.{k} 必填且非空")
    apps = d.get("apps")
    if not isinstance(apps, dict) or not apps:
        err("apps 必须是非空对象")
        apps = {}
    if len(apps) > 5000:
        err("单个源最多 5000 个应用")

    absolute_urls: list[str] = []
    manifest_targets: list[tuple[str, str, str]] = []

    for name, app in apps.items():
        w = f"apps.{name}"
        if not APPNAME_RE.match(name):
            err(f"{w}: appname 不合法（只允许字母/数字/点/下划线/短横线，且以字母或数字开头）")
        # 必填元数据
        for k in ("display_name", "desc", "platform", "categories", "icon_url", "run_as", "install_type", "is_docker"):
            if k not in app:
                err(f"{w}: 缺少必填字段 {k}")
        # platform
        pl = app.get("platform")
        pl = [pl] if isinstance(pl, str) else pl
        if not isinstance(pl, list) or not pl or any(x not in PLATFORMS for x in pl):
            err(f"{w}: platform 只允许 all/x86/arm")
        # categories
        cats = app.get("categories")
        if not isinstance(cats, list) or not (1 <= len(cats) <= 2) or any(c not in CATEGORIES for c in cats):
            err(f"{w}: categories 必须是 1~2 个固定分类")
        # 枚举 / 类型
        if app.get("run_as") not in ("package", "root"):
            err(f"{w}: run_as 只允许 package/root")
        if app.get("install_type") not in ("", "root"):
            err(f"{w}: install_type 只允许空字符串或 root")
        if not isinstance(app.get("is_docker"), bool):
            err(f"{w}: is_docker 必须是布尔值")
        if "service_port" in app and not isinstance(app["service_port"], str):
            err(f"{w}: service_port 必须是字符串")
        # URL 字段
        for k in ("icon_url", "readme_url", "bug_report_url"):
            if k in app:
                check_url(app[k], f"{w}.{k}")
                if isinstance(app[k], str) and app[k].startswith("http"):
                    absolute_urls.append(app[k])
        for i, u in enumerate(app.get("preview_urls", [])):
            check_url(u, f"{w}.preview_urls[{i}]")
            if isinstance(u, str) and u.startswith("http"):
                absolute_urls.append(u)
        if len(app.get("preview_urls", [])) > 8:
            warn(f"{w}: 预览图超过 8 张，客户端只会读取前 8 张")
        # i18n 基础字段仍需存在
        for loc, t in (app.get("i18n") or {}).items():
            if not isinstance(t, dict) or set(t) - {"display_name", "desc"}:
                err(f"{w}.i18n[{loc}]: 只能包含 display_name/desc")
        # releases
        rels = app.get("releases")
        if not isinstance(rels, dict) or not rels:
            err(f"{w}: 单文件模式必须提供 releases，且至少有一个版本")
            continue
        if len(rels) > 100:
            err(f"{w}: 单个应用最多 100 个版本")
        for ver, rel in rels.items():
            rw = f"{w}.releases.{ver}"
            if not isinstance(ver, str) or ver.lower() in ("latest", "newest"):
                err(f"{rw}: 版本号不能用 latest / 日期文字")
            if not isinstance(rel, dict):
                err(f"{rw}: 版本节点必须是对象")
                continue
            if "updated_at" in rel and not isinstance(rel["updated_at"], str):
                err(f"{rw}.updated_at 必须是字符串")
            pkgs = rel.get("packages")
            if not isinstance(pkgs, dict) or not pkgs:
                err(f"{rw}: 缺少有效的 packages")
                continue
            if set(pkgs) - ARCHS:
                err(f"{rw}: packages 架构键只允许 all/x86/arm，发现 {set(pkgs) - ARCHS}")
            for arch, pkg in pkgs.items():
                pw = f"{rw}.packages.{arch}"
                if not isinstance(pkg, dict):
                    err(f"{pw}: 安装包分支必须是对象")
                    continue
                if "download_url" not in pkg:
                    err(f"{pw}: 缺少 download_url（不能从其它分支继承）")
                else:
                    check_url(pkg["download_url"], f"{pw}.download_url")
                    if isinstance(pkg["download_url"], str) and pkg["download_url"].startswith("http"):
                        absolute_urls.append(pkg["download_url"])
                if "sha256" in pkg and not SHA256_RE.match(str(pkg["sha256"])):
                    err(f"{pw}: sha256 必须是 64 位十六进制")
                if "size" in pkg and (not isinstance(pkg["size"], int) or isinstance(pkg["size"], bool) or pkg["size"] < 0):
                    err(f"{pw}: size 必须是非负整数（Bytes）")
            # 架构可用性
            pl_set = set(pl or [])
            if "all" not in pl_set and not (pl_set & (set(pkgs) - {"all"})) and "all" not in pkgs:
                err(f"{rw}: 声明的平台 {sorted(pl_set)} 没有对应的安装包分支")
            if "sha256" not in next(iter(pkgs.values()), {}):
                warn(f"{rw}: 有安装包缺少 sha256（强烈建议填写）")

        latest = sorted(rels, key=lambda v: tuple(int(x) if x.isdigit() else x for x in re.split(r"[.\-]", v)))[-1]
        infos.append(f"{name}: {len(rels)} 个版本，最新 {latest}，{sum(len(r.get('packages', {})) for r in rels.values())} 个安装包")
        # 推断上游仓库，供 --check-manifest 使用
        guess = "oesp-fanctl" if name == "oesp-fanctl" else "ipsense-fnos"
        manifest_targets.append((name, guess, latest))

    if args.check_manifest:
        for name, repo, latest in manifest_targets:
            check_manifest(name, repo, latest)

    if args.check_urls:
        urls = sorted(set(absolute_urls))
        print(f"HEAD 检查 {len(urls)} 个绝对 URL …")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(head_url, urls))
        failed = [f"{u} -> {r}" for u, r in results if r.startswith("FAIL")]
        ok = len(results) - len(failed)
        infos.append(f"URL HEAD 检查：{ok} 个可达 / {len(failed)} 个失败")
        for f in failed[:20]:
            err(f"URL 不可达：{f}")

    print("\n".join("  · " + x for x in infos))
    if warns:
        print("\n警告：")
        print("\n".join("  ! " + x for x in warns))
    if errors:
        print("\n错误：")
        print("\n".join("  ✗ " + x for x in errors))
        print(f"\n校验未通过：{len(errors)} 个错误，{len(warns)} 个警告")
        return 1
    print(f"\n✓ 校验通过：{len(apps)} 个应用，{len(warns)} 个警告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
