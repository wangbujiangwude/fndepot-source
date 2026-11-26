#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""刷新 jsDelivr CDN 缓存，并可核对 CDN 内容与本地 fnpack.json 是否一致。

GitHub 仓库根地址模式会经 CDN 加速读取 fnpack.json；CDN 对 @main 分支缓存较长，
源更新后需要主动 purge，否则用户仍会看到旧版本列表。

用法：
  python scripts/purge_cdn.py            # 仅刷新缓存
  python scripts/purge_cdn.py --check   # 刷新并核对两个 CDN 节点与本地一致
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "wangbujiangwude/fndepot-source"
PURGE = f"https://purge.jsdelivr.net/gh/{REPO}@main/fnpack.json"
CDNS = [
    f"https://cdn.jsdelivr.net/gh/{REPO}@main/fnpack.json",
    f"https://fastly.jsdelivr.net/gh/{REPO}@main/fnpack.json",
]


def get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "fndepot-purge/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="刷新后核对 CDN 内容与本地 fnpack.json 一致")
    args = ap.parse_args()

    try:
        res = json.loads(get(PURGE))
    except Exception as e:
        print(f"purge 请求失败: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(f"purge: status={res.get('status')} id={res.get('id')}")
    for path, info in res.get("paths", {}).items():
        print(f"  {path}: throttled={info.get('throttled')} providers={info.get('providers')}")
    if res.get("status") != "finished":
        print("purge 未成功完成", file=sys.stderr)
        return 1

    if not args.check:
        return 0

    local = (ROOT / "fnpack.json").read_bytes()
    all_ok = True
    for u in CDNS:
        body = b""
        ok = False
        for _ in range(4):
            try:
                body = get(u)
                ok = body == local
                if ok:
                    break
            except Exception:
                pass
            time.sleep(2)
        print(f"  {'OK' if ok else 'FAIL'}  {u.split('/')[2]}  CDN={len(body)}B 本地={len(local)}B")
        all_ok = all_ok and ok
    print("全部 CDN 节点与本地一致" if all_ok else "仍有 CDN 节点未更新，稍后重试")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
