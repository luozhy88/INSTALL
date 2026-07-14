#!/usr/bin/env python3
"""补译工具：为已抓取但缺译文的 JSON 结果补齐翻译并重新生成 HTML 报告。

用法：
    python3 04_backfill_translate.py output/my_accounts_recent_posts_20260712_111127.json
    python3 04_backfill_translate.py output/xxx.json --target my_accounts --email
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("scraper", BASE / "01_x_following_scraper.py")
scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper)


def main():
    ap = argparse.ArgumentParser(description="补译 JSON 结果并重新生成报告")
    ap.add_argument("json_file", help="抓取结果 JSON 文件路径")
    ap.add_argument("--target", default=None, help="报告标题（默认从文件名推断）")
    ap.add_argument("--images", action="store_true", help="同时下载推文图片（供报告/邮件内嵌）")
    ap.add_argument("--email", action="store_true", help="补译完成后发送邮件报告")
    args = ap.parse_args()

    path = Path(args.json_file)
    posts = json.loads(path.read_text(encoding="utf-8"))
    missing = [p for p in posts if (p.get("text") or "").strip() and not p.get("text_translated")]
    print(f"共 {len(posts)} 条，待补译 {len(missing)} 条")

    if missing:
        scraper.translate_posts(posts, delay=0.5)
        path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已回写：{path}")

    if args.images:
        scraper.download_images(posts)
        path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")

    target = args.target or path.stem.replace("_recent_posts", "").rsplit("_", 2)[0]
    rp = scraper.generate_html_report(posts, target)
    print(f"报告已生成：{rp}")

    if args.email:
        ok = scraper.send_report_email(rp, posts, target)
        print("邮件发送：" + ("成功" if ok else "失败（未配置或出错）"))


if __name__ == "__main__":
    sys.exit(main())
