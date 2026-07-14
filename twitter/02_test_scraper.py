#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_test_scraper.py — 对 01_x_following_scraper.py 的自动化测试

测试内容：
  1. 真实浏览器启动 + 访问 x.com
  2. 登录用户名识别（模拟页）
  3. 关注用户信息解析（模拟页）
  4. 关注列表保存 CSV/JSON
  5. 互动计数单位换算（K / M / 万 / 逗号 / 空）
  6. 推文内容解析：7 种典型推文（emoji/话题/视频/转发/零互动/纯图/长文）
  7. 推文保存 CSV/JSON + 回读校验
"""

import csv
import importlib.util
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_FOLLOWING = os.path.join(BASE_DIR, "tests", "mock_following_page.html")
MOCK_PROFILE = os.path.join(BASE_DIR, "tests", "mock_user_profile.html")

spec = importlib.util.spec_from_file_location("scraper", os.path.join(BASE_DIR, "01_x_following_scraper.py"))
scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper)

PASS, FAIL = [], []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f"  ✓ {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL.append(name)
        print(f"  ✗ {name}" + (f" — {detail}" if detail else ""))


def section(title):
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


def main():
    driver = None
    try:
        # ---------- 测试 1：真实浏览器 ----------
        section("测试 1：启动 Chrome 并访问 x.com（真实网络）")
        driver = scraper.build_driver()
        driver.get("https://x.com/home")
        import time
        time.sleep(4)
        check("Chrome 自动启动成功", True)
        check("成功访问 x.com", "x.com" in driver.current_url, f"URL={driver.current_url}")

        # ---------- 测试 2：用户名识别 ----------
        section("测试 2：关注列表页 —— 登录用户名识别")
        driver.get("file://" + MOCK_FOLLOWING)
        time.sleep(1)
        username = scraper.get_my_username(driver)
        check("从导航栏获取登录用户名", username == "testuser888", f"得到={username}")

        # ---------- 测试 3：用户信息解析 ----------
        section("测试 3：关注用户信息解析")
        cells = driver.find_elements(scraper.By.CSS_SELECTOR, scraper.USER_CELL_SELECTOR)
        users = {}
        for c in cells:
            info = scraper.parse_user_cell(c)
            if info:
                users[info["handle"]] = info
        check("解析出 4 个关注用户", len(users) == 4, f"实际={len(users)}")
        u1 = users.get("@elonmusk")
        check("认证用户解析正确", u1 is not None and u1["name"] == "Elon Musk"
              and u1["bio"] == "Technoking of Tesla, Imperator of Mars" and u1["verified"] is True)
        u3 = users.get("@nobio_user")
        check("无简介用户：按钮文字未被误抓", u3 is not None and u3["bio"] == "")

        # ---------- 测试 4：关注列表保存 ----------
        section("测试 4：关注列表保存 CSV / JSON")
        json_path, csv_path = scraper.save_results(list(users.values()), "testuser888")
        with open(json_path, encoding="utf-8") as f:
            check("关注列表 JSON 条数正确", len(json.load(f)) == 4)
        with open(csv_path, encoding="utf-8-sig") as f:
            check("关注列表 CSV 条数正确", len(list(csv.DictReader(f))) == 4)

        # ---------- 测试 5：计数单位换算 ----------
        section("测试 5：互动计数单位换算 parse_count()")
        cases = [
            ("12.5K", 12500), ("892.3K", 892300), ("1.5M", 1500000),
            ("3.4万", 34000), ("15.6万", 156000), ("2,104", 2104),
            ("523", 523), ("", 0), ("  ", 0), ("abc", 0),
        ]
        all_ok = True
        for raw, expect in cases:
            got = scraper.parse_count(raw)
            ok = got == expect
            all_ok = all_ok and ok
            check(f"parse_count({raw!r}) == {expect}", ok, f"得到={got}")

        # ---------- 测试 6：推文解析 ----------
        section("测试 6：用户主页推文解析（7 种典型推文）")
        driver.get("file://" + MOCK_PROFILE)
        tweets = scraper.collect_tweets(driver, max_posts=0)
        by_id = {t["tweet_id"]: t for t in tweets}
        check("共解析出 8 条推文", len(tweets) == 8, f"实际={len(tweets)}")

        t1 = by_id.get("1912345678901234567")
        check("推文1 链接与ID", t1 is not None
              and t1["url"] == "https://x.com/elonmusk/status/1912345678901234567")
        if t1:
            check("推文1 作者信息", t1["author_name"] == "Elon Musk" and t1["author_handle"] == "@elonmusk")
            check("推文1 发布时间", t1["posted_at"] == "2026-07-10T08:15:30.000Z")
            check("推文1 含 emoji 原文", "🚀" in t1["text"])
            check("推文1 含话题标签", "#SpaceX" in t1["text"] and "#Mars" in t1["text"])
            check("推文1 互动数(K换算)",
                  t1["reply_count"] == 12500 and t1["retweet_count"] == 48200 and t1["like_count"] == 892300)
            check("推文1 图片标记", t1["has_photo"] is True and t1["has_video"] is False)
            check("推文1 非转发", t1["is_retweet"] is False)

        t2 = by_id.get("1923456789012345678")
        check("推文2 中文内容+@提及", t2 is not None and "@hanmeimei" in t2["text"] and "AI 编程助手" in t2["text"])
        if t2:
            check("推文2 中文'万'计数换算",
                  t2["reply_count"] == 34000 and t2["retweet_count"] == 12000 and t2["like_count"] == 156000)
            check("推文2 视频标记", t2["has_video"] is True and t2["has_photo"] is False)

        t3 = by_id.get("1934567890123456789")
        check("推文3 外链推文", t3 is not None and "t.co/abc123xyz" in t3["text"])
        if t3:
            check("推文3 逗号数字换算 2,104→2104", t3["like_count"] == 2104)
            check("推文3 普通整数", t3["reply_count"] == 523 and t3["retweet_count"] == 89)

        t4 = by_id.get("1945678901234567890")
        check("推文4 转发识别", t4 is not None and t4["is_retweet"] is True)
        if t4:
            check("推文4 原作者保留", t4["author_handle"] == "@ai_researcher")

        t5 = by_id.get("1956789012345678901")
        check("推文5 零互动→0", t5 is not None
              and t5["reply_count"] == 0 and t5["retweet_count"] == 0 and t5["like_count"] == 0)
        if t5:
            check("推文5 含 emoji 的中文内容", "Hello World" in t5["text"] and "🎉" in t5["text"])

        t6 = by_id.get("1967890123456789012")
        check("推文6 纯图片推文未被丢弃", t6 is not None and t6["text"] == "" and t6["has_photo"] is True)

        t7 = by_id.get("1978901234567890123")
        check("推文7 多段长文保留换行", t7 is not None
              and "1. 每天固定时间写" in t7["text"] and "3. 多读经典" in t7["text"]
              and "\n" in t7["text"])

        t8 = by_id.get("1989012345678901234")
        check("推文8 置顶识别（is_pinned=True）", t8 is not None and t8["is_pinned"] is True)
        check("推文8 置顶不误判为转发", t8 is not None and t8["is_retweet"] is False)

        # 去重验证：页面再收集一次，数量不应翻倍
        tweets2 = scraper.collect_tweets(driver, max_posts=0)
        check("重复收集不产生重复推文", len(tweets2) == 8, f"实际={len(tweets2)}")

        # max_posts 截断验证
        driver.get("file://" + MOCK_PROFILE)
        tweets3 = scraper.collect_tweets(driver, max_posts=3)
        check("max_posts=3 截断生效", len(tweets3) == 3, f"实际={len(tweets3)}")

        # since_days 按天过滤验证（与脚本用同一时间基准计算期望值）
        from datetime import datetime as _dt, timedelta as _td, timezone as _tz
        driver.get("file://" + MOCK_PROFILE)
        cutoff = _dt.now(_tz.utc) - _td(days=4)
        expected = {t["tweet_id"] for t in tweets
                    if scraper._parse_dt(t["posted_at"]) and scraper._parse_dt(t["posted_at"]) >= cutoff}
        tweets4 = scraper.collect_tweets(driver, max_posts=0, since_days=4)
        got4 = {t["tweet_id"] for t in tweets4}
        check("since_days=4 只保留最近 4 天推文", got4 == expected,
              f"应保留 {len(expected)} 条，实际 {len(got4)} 条")
        check("过滤结果中无超期推文",
              all(scraper._parse_dt(t["posted_at"]) >= cutoff for t in tweets4))

        # 账号清单文件读取验证（数量动态比对，清单可随时编辑）
        acc_path = os.path.join(BASE_DIR, "accounts.txt")
        accs = scraper.load_accounts(acc_path)
        expected_n = sum(1 for ln in open(acc_path, encoding="utf-8")
                         if ln.strip() and not ln.strip().startswith("#"))
        check("accounts.txt 读取账号数正确", len(accs) == expected_n and expected_n > 0,
              f"实际={accs}")
        check("账号 @ 前缀正确去除", all(not a.startswith("@") for a in accs))

        # ---------- 测试 7：推文保存 ----------
        section("测试 7：推文结果保存 CSV / JSON + 回读校验")
        pj, pc = scraper.save_posts(tweets, "testuser888")
        check("推文 JSON 文件已生成", os.path.exists(pj), pj)
        check("推文 CSV 文件已生成", os.path.exists(pc), pc)
        with open(pj, encoding="utf-8") as f:
            jdata = json.load(f)
        check("推文 JSON 条数=8", len(jdata) == 8)
        expect_fields = {"tweet_id", "url", "author_name", "author_handle", "posted_at", "text",
                         "reply_count", "retweet_count", "like_count", "has_photo", "has_video",
                         "image_urls", "is_retweet", "is_pinned"}
        check("推文 JSON 字段完整", all(set(t) == expect_fields for t in jdata))
        with open(pc, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        check("推文 CSV 条数=8", len(rows) == 8)
        check("推文 CSV 计数与 JSON 一致",
              int(rows[0]["like_count"]) == jdata[0]["like_count"] and
              rows[0]["text"] == jdata[0]["text"])

        # ---------- 测试 8：多账号侧边栏报告 ----------
        section("测试 8：多账号 HTML 报告（侧边栏导航）")
        rp = scraper.generate_html_report(tweets, "test_multi")
        check("报告文件已生成", os.path.exists(rp), rp)
        with open(rp, encoding="utf-8") as f:
            html = f.read()
        n_accounts = len({t["author_handle"] for t in tweets})
        check("报告含侧边栏", 'aside class="nav"' in html)
        check("侧边栏含每个账号的导航项",
              all(f'acc-{h.lstrip("@")}' in html for h in {t["author_handle"] for t in tweets}),
              f"共 {n_accounts} 个账号")
        check("多账号标题正确", "我的关注 · 推文报告" in html)
        check("置顶推文显示置顶徽章", "📌 置顶" in html)
        check("按账号分组区块存在", html.count('<section class="group"') == n_accounts)

    except Exception as e:
        print(f"\n测试过程中发生异常：{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        FAIL.append("测试异常中断")
    finally:
        if driver:
            driver.quit()

    print()
    print("=" * 64)
    print(f"测试结果：通过 {len(PASS)} 项，失败 {len(FAIL)} 项")
    if FAIL:
        print("失败项：" + "、".join(FAIL))
    else:
        print("🎉 全部测试通过！用户信息抓取 + 推文抓取逻辑均工作正常。")
    print("=" * 64)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
