#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_x_following_scraper.py

自动打开谷歌浏览器，登录 X (Twitter) 账户后，
抓取当前账户【关注列表】中的用户信息，并保存到本地。

功能：
  1. 自动启动 Google Chrome 并打开 https://x.com/home
  2. 等待你在浏览器中手动登录（首次需要，之后会复用登录状态）
  3. 自动进入你的“正在关注”列表页面
  4. 滚动抓取每个关注用户的：昵称、用户名(@handle)、简介、是否认证
  5. （可选）逐个打开关注用户的主页，抓取他们最近发表的推文内容：
     推文文字、发布时间、评论/转发/点赞数、是否含图片/视频、是否转发
  6. 结果保存为 CSV 和 JSON 两个文件（保存在脚本同目录下的 output/ 文件夹）

用法：
  python3 01_x_following_scraper.py                      # 默认最多抓取 200 个关注用户
  python3 01_x_following_scraper.py --max 50             # 最多抓取 50 个关注用户
  python3 01_x_following_scraper.py --max 0              # 不限制，抓到列表尽头
  python3 01_x_following_scraper.py --posts 10           # 额外抓取每个用户最近 10 条推文
  python3 01_x_following_scraper.py --posts 10 --posts-users 5  # 只抓前 5 个用户的推文

依赖：selenium（已安装），Chrome 浏览器（drivers/ 下已备好匹配的 ChromeDriver）
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(BASE_DIR, "chrome_profile_x")   # 保存登录状态的 Chrome 配置目录
OUTPUT_DIR = os.path.join(BASE_DIR, "output")              # 抓取结果输出目录
STATE_PATH = os.path.join(OUTPUT_DIR, "state.json")        # 增量抓取状态（每账号上次最新推文ID）
EMAIL_CONFIG_PATH = os.path.join(BASE_DIR, "email_config.json")  # 邮箱配置（含授权码，勿外传）

PROFILE_LINK_SELECTOR = 'a[data-testid="AppTabBar_Profile_Link"]'
USER_CELL_SELECTOR = 'div[data-testid="UserCell"]'
TWEET_SELECTOR = 'article[data-testid="tweet"]'


def build_driver():
    """启动 Chrome，使用独立配置目录以保留登录状态。

    优先使用脚本同目录下 drivers/chromedriver（国内网络无法自动下载驱动，
    已提前手动下载好）；若不存在则回退到 Selenium 自动下载。
    """
    opts = Options()
    opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--start-maximized")
    opts.add_argument("--lang=zh-CN")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    # Windows 用 chromedriver.exe，macOS/Linux 用 chromedriver
    driver_name = "chromedriver.exe" if sys.platform == "win32" else "chromedriver"
    local_driver = os.path.join(BASE_DIR, "drivers", driver_name)
    if os.path.exists(local_driver):
        service = Service(executable_path=local_driver)
        driver = webdriver.Chrome(service=service, options=opts)
    else:
        driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(60)
    return driver


def wait_for_login(driver, timeout=600):
    """等待用户完成登录：检测左侧导航栏是否出现个人主页链接。"""
    print("=" * 60)
    print("请在打开的 Chrome 窗口中登录你的 X 账户。")
    print("登录成功并进入首页后，脚本会自动继续（最长等待 10 分钟）...")
    print("=" * 60)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, PROFILE_LINK_SELECTOR))
    )
    print("检测到已登录。")


def get_my_username(driver):
    """从左侧导航栏的个人主页链接中获取当前登录用户名。"""
    try:
        link = driver.find_element(By.CSS_SELECTOR, PROFILE_LINK_SELECTOR)
        href = link.get_attribute("href") or ""
        username = href.rstrip("/").split("/")[-1]
        return username
    except NoSuchElementException:
        return None


def parse_user_cell(cell):
    """从一个 UserCell 元素中解析用户信息，解析失败返回 None。"""
    try:
        text = cell.text or ""
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        handle = ""
        for ln in lines:
            if ln.startswith("@"):
                m = re.match(r"@[A-Za-z0-9_]{1,20}", ln)
                handle = m.group(0) if m else ln
                break
        if not handle:
            links = cell.find_elements(By.CSS_SELECTOR, 'a[href]')
            for a in links:
                h = a.get_attribute("href") or ""
                m = re.search(r"x\.com/([A-Za-z0-9_]{1,20})$", h)
                if m:
                    handle = "@" + m.group(1)
                    break
        if not handle:
            return None

        # 昵称：第一个不是 @handle 的行
        name = ""
        for ln in lines:
            if not ln.startswith("@"):
                name = ln
                break

        # 简介：@handle 之后的内容（去掉“关注/正在关注”等按钮文字）
        bio_lines = []
        past_handle = False
        for ln in lines:
            if past_handle:
                if ln in ("关注", "正在关注", "Follow", "Following", "回关", "Follow back"):
                    continue
                bio_lines.append(ln)
            if ln.startswith("@"):
                past_handle = True
        bio = " ".join(bio_lines)

        # 是否认证（蓝/金/灰标）
        verified = False
        try:
            verified = len(cell.find_elements(By.CSS_SELECTOR, 'svg[data-testid="icon-verified"]')) > 0
        except Exception:
            pass

        return {
            "name": name,
            "handle": handle,
            "bio": bio,
            "verified": verified,
            "profile_url": f"https://x.com/{handle.lstrip('@')}",
        }
    except StaleElementReferenceException:
        return None
    except Exception:
        return None


def scrape_following(driver, username, max_users):
    """进入关注列表页，滚动抓取用户信息。"""
    url = f"https://x.com/{username}/following"
    print(f"正在打开关注列表页面：{url}")
    driver.get(url)

    # 等待第一个用户卡片出现（登录后首次跳转可能较慢，超时则刷新重试一次）
    for attempt in range(2):
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, USER_CELL_SELECTOR))
            )
            break
        except Exception:
            if attempt == 0:
                print("页面加载较慢，刷新重试一次...")
                driver.refresh()
            else:
                raise
    time.sleep(2)

    users = {}          # handle -> info，用于去重
    no_new_rounds = 0   # 连续没有新用户的滚动轮数
    round_no = 0

    while True:
        round_no += 1
        cells = driver.find_elements(By.CSS_SELECTOR, USER_CELL_SELECTOR)
        new_count = 0
        for cell in cells:
            info = parse_user_cell(cell)
            if info and info["handle"] not in users:
                users[info["handle"]] = info
                new_count += 1

        print(f"第 {round_no} 轮：本轮新增 {new_count} 个，累计 {len(users)} 个用户")

        if max_users and len(users) >= max_users:
            print(f"已达到上限 {max_users} 个用户，停止抓取。")
            break

        if new_count == 0:
            no_new_rounds += 1
            if no_new_rounds >= 5:
                print("连续多轮没有新用户，已到达列表末尾，停止抓取。")
                break
        else:
            no_new_rounds = 0

        # 滚动到页面底部加载更多
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2.5)

    result = list(users.values())
    if max_users:
        result = result[:max_users]
    return result


def save_results(users, username):
    """保存结果为 CSV 和 JSON。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(OUTPUT_DIR, f"{username}_following_{stamp}.json")
    csv_path = os.path.join(OUTPUT_DIR, f"{username}_following_{stamp}.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "handle", "bio", "verified", "profile_url"])
        writer.writeheader()
        writer.writerows(users)

    return json_path, csv_path


# ============================ 推文抓取 ============================

def parse_count(text):
    """把页面上的互动计数转成整数，支持 1.2K / 3.4M / 2.5万 / 空 等写法。"""
    if not text:
        return 0
    text = text.strip().replace(",", "")
    m = re.match(r"^([\d.]+)\s*([KkMm万千億亿]?)$", text)
    if not m:
        return 0
    num = float(m.group(1))
    unit = m.group(2)
    if unit in ("K", "k", "千"):
        num *= 1_000
    elif unit in ("M", "m"):
        num *= 1_000_000
    elif unit == "万":
        num *= 10_000
    elif unit in ("億", "亿"):
        num *= 100_000_000
    return int(num)


def _find_count(article, testid):
    """从推文卡片的按钮中读取互动计数。"""
    try:
        btn = article.find_element(By.CSS_SELECTOR, f'button[data-testid="{testid}"]')
        return parse_count(btn.text)
    except NoSuchElementException:
        return 0
    except StaleElementReferenceException:
        return 0


def parse_tweet(article):
    """从一条推文 article 元素中解析内容，解析失败返回 None。"""
    try:
        # 推文链接与 ID：发布时间外面包裹的 a 标签指向推文详情页
        tweet_id, tweet_url = "", ""
        posted_at = ""
        try:
            time_el = article.find_element(By.CSS_SELECTOR, "time")
            posted_at = time_el.get_attribute("datetime") or ""
            link_el = time_el.find_element(By.XPATH, "./ancestor::a[1]")
            href = link_el.get_attribute("href") or ""
            m = re.search(r"/(status|statuses)/(\d+)", href)
            if m:
                tweet_id = m.group(2)
                tweet_url = href.split("?")[0]
        except NoSuchElementException:
            pass

        # 作者信息（注意：@handle 和 “· 日期” 常渲染在同一行，需用正则精确提取）
        author_name, author_handle = "", ""
        try:
            name_block = article.find_element(By.CSS_SELECTOR, 'div[data-testid="User-Name"]')
            block_text = name_block.text or ""
            m = re.search(r"@[A-Za-z0-9_]{1,20}", block_text)
            if m:
                author_handle = m.group(0)
            for ln in [l.strip() for l in block_text.split("\n") if l.strip()]:
                if not ln.startswith("@") and not ln.startswith("·"):
                    author_name = ln
                    break
            if not author_handle:
                for a in name_block.find_elements(By.CSS_SELECTOR, 'a[href]'):
                    h = a.get_attribute("href") or ""
                    m = re.search(r"x\.com/([A-Za-z0-9_]{1,20})$", h)
                    if m:
                        author_handle = "@" + m.group(1)
                        break
        except NoSuchElementException:
            pass

        # 推文正文（长推文会被折叠，先点“Show more/显示更多”展开再读全文）
        try:
            show_more = article.find_element(By.CSS_SELECTOR, 'div[data-testid="tweet-text-show-more-link"]')
            article.parent.execute_script("arguments[0].click();", show_more)
            time.sleep(0.4)
        except NoSuchElementException:
            pass
        except StaleElementReferenceException:
            pass
        text = ""
        try:
            text_el = article.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
            text = (text_el.text or "").strip()
        except NoSuchElementException:
            pass

        # 媒体标记与图片 URL（统一换成 large 高清版本）
        photo_divs = article.find_elements(By.CSS_SELECTOR, 'div[data-testid="tweetPhoto"]')
        has_photo = len(photo_divs) > 0
        has_video = len(article.find_elements(By.CSS_SELECTOR, 'div[data-testid="videoComponent"]')) > 0
        image_urls = []
        for img in article.find_elements(By.CSS_SELECTOR, 'div[data-testid="tweetPhoto"] img[src]'):
            src = img.get_attribute("src") or ""
            if "pbs.twimg.com/media/" in src:
                if "name=" in src:
                    src = re.sub(r"name=\w+", "name=large", src)
                else:
                    src += ("&" if "?" in src else "?") + "name=large"
                if src not in image_urls:
                    image_urls.append(src)

        # 顶部提示条：区分“转发”与“置顶”（Pinned）
        is_retweet, is_pinned = False, False
        try:
            sc = article.find_elements(By.CSS_SELECTOR, 'div[data-testid="socialContext"]')
            sc_text = sc[0].text if sc else ""
            is_pinned = ("Pinned" in sc_text) or ("置顶" in sc_text)
            is_retweet = bool(sc_text) and not is_pinned
        except Exception:
            pass

        if not tweet_id and not text:
            return None

        return {
            "tweet_id": tweet_id,
            "url": tweet_url,
            "author_name": author_name,
            "author_handle": author_handle,
            "posted_at": posted_at,
            "text": text,
            "reply_count": _find_count(article, "reply"),
            "retweet_count": _find_count(article, "retweet"),
            "like_count": _find_count(article, "like"),
            "has_photo": has_photo,
            "has_video": has_video,
            "image_urls": image_urls,
            "is_retweet": is_retweet,
            "is_pinned": is_pinned,
        }
    except StaleElementReferenceException:
        return None
    except Exception:
        return None


def _parse_dt(iso):
    """解析 ISO 时间字符串为带时区的 datetime，失败返回 None。"""
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def collect_tweets(driver, max_posts, since_days=None, since_id=None):
    """在当前页面（用户主页）滚动收集推文，按 tweet_id 去重。

    since_days: 只保留最近 N 天发表的推文；遇到更早的推文即停止滚动。
    since_id:   只保留 ID 大于该值的推文（增量模式）；遇到旧推文即停止滚动。
    """
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, TWEET_SELECTOR))
    )
    time.sleep(2)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=since_days)) if since_days else None
    since_id_int = int(since_id) if since_id and str(since_id).isdigit() else None
    tweets = {}
    no_new_rounds = 0
    while True:
        articles = driver.find_elements(By.CSS_SELECTOR, TWEET_SELECTOR)
        new_count = 0
        oldest_seen = None    # 本轮页面中（非置顶）推文里的最早时间
        oldest_id = None      # 本轮页面中（非置顶）推文里的最小 ID
        for art in articles:
            info = parse_tweet(art)
            if not info:
                continue
            dt = _parse_dt(info["posted_at"])
            tid = int(info["tweet_id"]) if info["tweet_id"].isdigit() else None
            if not info.get("is_pinned"):
                if dt and (oldest_seen is None or dt < oldest_seen):
                    oldest_seen = dt
                if tid and (oldest_id is None or tid < oldest_id):
                    oldest_id = tid
            if cutoff and (dt is None or dt < cutoff):
                continue  # 超出时间范围（或无时间的广告推文）
            if since_id_int and tid and tid <= since_id_int:
                continue  # 上次已经抓过的旧推文
            key = info["tweet_id"] or info["url"] or (info["text"][:50] + info["posted_at"])
            if key not in tweets:
                tweets[key] = info
                new_count += 1

        if max_posts and len(tweets) >= max_posts:
            break
        if cutoff and oldest_seen and oldest_seen < cutoff:
            break  # 时间线是按时间倒序的，再往下只会更早
        if since_id_int and oldest_id and oldest_id <= since_id_int:
            break  # 已滚动到上次抓取过的位置
        if new_count == 0:
            no_new_rounds += 1
            if no_new_rounds >= 3:
                break
        else:
            no_new_rounds = 0

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    result = list(tweets.values())
    return result[:max_posts] if max_posts else result


def scrape_recent_posts(driver, handle, max_posts, since_days=None, since_id=None):
    """打开某个用户的主页，抓取其最近发表的推文。"""
    url = f"https://x.com/{handle.lstrip('@')}"
    span = f"最近 {since_days} 天" if since_days else "最近"
    inc = "（增量）" if since_id else ""
    print(f"  正在抓取 {handle} {span}的推文{inc}：{url}")
    driver.get(url)
    try:
        tweets = collect_tweets(driver, max_posts, since_days=since_days, since_id=since_id)
    except Exception as e:
        print(f"  ⚠ {handle} 的推文抓取失败：{e}")
        tweets = []
    print(f"  {handle}：抓到 {len(tweets)} 条推文")
    return tweets


# ============================ 增量状态 ============================

def load_state():
    """读取增量抓取状态：每个账号上次见过的最新推文 ID。"""
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"accounts": {}}


def save_state(state):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ============================ 邮件发送 ============================

def load_email_config():
    """读取邮箱配置；文件不存在或授权码未填写时返回 None。"""
    if not os.path.exists(EMAIL_CONFIG_PATH):
        return None
    try:
        with open(EMAIL_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        if not cfg.get("auth_code") or "填写" in str(cfg.get("auth_code")):
            return None
        return cfg
    except Exception:
        return None


def build_self_contained_html(report_path, max_px=1280, quality=72):
    """把报告中的本地图片引用替换为 base64 数据，生成单文件自包含 HTML。

    为控制邮件附件大小（QQ 邮箱限制约 50MB），嵌入前用 Pillow 压缩图片：
    最长边缩放到 max_px、JPEG 质量 quality；压缩无效或 Pillow 不可用时回退原图。
    """
    import base64
    import io
    import mimetypes

    try:
        from PIL import Image
    except ImportError:
        Image = None

    def _embed(fpath):
        """返回 (mime, base64)：优先使用压缩后的 JPEG。"""
        with open(fpath, "rb") as f:
            raw = f.read()
        if Image:
            try:
                with Image.open(fpath) as im:
                    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                        im = im.convert("RGBA")
                        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
                        im = Image.alpha_composite(bg, im).convert("RGB")
                    elif im.mode != "RGB":
                        im = im.convert("RGB")
                    im.thumbnail((max_px, max_px))
                    buf = io.BytesIO()
                    im.save(buf, "JPEG", quality=quality)
                    data = buf.getvalue()
                if len(data) < len(raw):
                    return "image/jpeg", base64.b64encode(data).decode("ascii")
            except Exception:
                pass
        mime = mimetypes.guess_type(fpath)[0] or "image/jpeg"
        return mime, base64.b64encode(raw).decode("ascii")

    with open(report_path, encoding="utf-8") as f:
        html = f.read()
    for rel in dict.fromkeys(re.findall(r'(?:src|href)="(images/[^"]+)"', html)):
        fpath = os.path.join(OUTPUT_DIR, rel)
        if not os.path.exists(fpath):
            continue
        mime, b64 = _embed(fpath)
        html = html.replace(f'src="{rel}"', f'src="data:{mime};base64,{b64}"')
        html = html.replace(f'href="{rel}"', f'href="data:{mime};base64,{b64}"')
    return html


def send_report_email(report_path, posts, target):
    """把报告以附件形式发送到邮箱。

    附件为自包含 HTML（图片已 base64 嵌入），下载后双击即可在浏览器中
    查看完整报告；邮件正文附带摘要与热门推文列表。
    """
    import smtplib
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.header import Header
    from email.utils import formataddr
    import html as _html

    cfg = load_email_config()
    if not cfg:
        print("📧 未配置邮箱（email_config.json 缺失或授权码未填写），跳过发送。")
        return False

    n_accounts = len({p.get("author_handle") for p in posts})
    total_like = sum(p.get("like_count", 0) for p in posts)

    # 邮件正文：摘要 + 每账号统计 + 点赞 Top5
    per_acc = {}
    for p in posts:
        h = p.get("author_handle") or "@unknown"
        per_acc[h] = per_acc.get(h, 0) + 1
    acc_rows = "".join(
        f"<tr><td>{_html.escape(h)}</td><td style='text-align:center'>{c}</td></tr>"
        for h, c in per_acc.items())
    top5 = sorted(posts, key=lambda p: p.get("like_count", 0), reverse=True)[:5]
    top_rows = "".join(
        f"<tr><td>{_html.escape(p.get('author_handle',''))}</td>"
        f"<td style='text-align:center'>❤️ {p.get('like_count',0)}</td>"
        f"<td><a href='{_html.escape(p.get('url',''))}'>{_html.escape((p.get('text') or '')[:50])}…</a></td></tr>"
        for p in top5)
    body = f"""<html><body style="font-family:-apple-system,'PingFang SC',sans-serif;color:#0f1419">
    <h2 style="color:#1d9bf0">📊 X 推文报告 · {datetime.now().strftime('%Y-%m-%d %H:%M')}</h2>
    <p>共 <b>{len(posts)}</b> 条推文 · <b>{n_accounts}</b> 个账号 · ❤️ 总点赞 <b>{total_like}</b></p>
    <h3>各账号推文数</h3>
    <table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;border-color:#e6ecf0">
      <tr style="background:#f5f8fa"><th>账号</th><th>条数</th></tr>{acc_rows}
    </table>
    <h3>🔥 点赞 Top 5</h3>
    <table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;border-color:#e6ecf0">
      <tr style="background:#f5f8fa"><th>账号</th><th>点赞</th><th>内容</th></tr>{top_rows}
    </table>
    <p style="margin-top:20px;padding:12px;background:#f0f7fd;border-left:3px solid #1d9bf0">
      📎 <b>完整报告请下载附件 HTML 文件</b>，双击即可在浏览器中打开（图片已嵌入文件内部，无需联网）：<br/>
      侧边栏账号导航 · 中英互译 · 高清图片 · 互动数据，完整体验尽在附件中。
    </p>
    </body></html>"""

    # 自包含报告附件（图片压缩嵌入；仍超 40MB 则自动进一步降质，防止邮箱拒收）
    for max_px, quality in [(1280, 72), (960, 60), (640, 50)]:
        sc_html = build_self_contained_html(report_path, max_px, quality)
        size_mb = len(sc_html.encode("utf-8")) / 1024 / 1024
        if size_mb <= 40:
            break
        print(f"  ⚠ 附件 {size_mb:.1f}MB 超限，降质重试（{max_px}px/q{quality} → 更小）")

    msg = MIMEMultipart("mixed")
    msg["From"] = formataddr((str(Header("X推文报告", "utf-8")), cfg["sender"]))
    msg["To"] = cfg["recipient"]
    msg["Subject"] = Header(
        f"【X推文报告】{datetime.now().strftime('%m-%d %H:%M')} · {len(posts)}条推文 / {n_accounts}个账号", "utf-8")
    msg.attach(MIMEText(body, "html", "utf-8"))

    fname = os.path.basename(report_path)
    part = MIMEApplication(sc_html.encode("utf-8"), _subtype="html", Name=fname)
    part["Content-Disposition"] = f'attachment; filename="{fname}"'
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL(cfg["smtp_host"], int(cfg["smtp_port"]), timeout=180) as smtp:
            smtp.login(cfg["sender"], cfg["auth_code"])
            smtp.sendmail(cfg["sender"], [cfg["recipient"]], msg.as_string())
        print(f"📧 报告已发送到 {cfg['recipient']}（{len(posts)} 条推文，自包含附件 {size_mb:.1f}MB）")
        return True
    except Exception as e:
        print(f"⚠ 邮件发送失败：{e}")
        return False


def notify_macos(title, message):
    """发送桌面系统通知：macOS 用 osascript；Windows 暂不弹通知（失败静默忽略）。"""
    if sys.platform != "darwin":
        return
    import subprocess
    safe = lambda s: s.replace('"', "'")[:120]
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{safe(message)}" with title "{safe(title)}"'],
                       timeout=10)
    except Exception:
        pass


def load_accounts(path):
    """从 txt 文件读取账号清单（忽略空行和 # 注释行）。"""
    accounts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                accounts.append(line.lstrip("@"))
    return accounts


def save_posts(posts, username):
    """保存推文结果为 CSV 和 JSON。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(OUTPUT_DIR, f"{username}_recent_posts_{stamp}.json")
    csv_path = os.path.join(OUTPUT_DIR, f"{username}_recent_posts_{stamp}.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    fields = ["tweet_id", "url", "author_name", "author_handle", "posted_at", "text",
              "reply_count", "retweet_count", "like_count", "has_photo", "has_video",
              "image_urls", "local_images", "text_translated", "is_retweet", "is_pinned"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for p in posts:
            row = dict(p)
            row["image_urls"] = " ".join(p.get("image_urls", []))
            row["local_images"] = " ".join(p.get("local_images", []))
            writer.writerow(row)

    return json_path, csv_path


# ============================ 中英互译 ============================

def _translate_chunk(text, sl, tl):
    """调用 MyMemory 免费翻译接口（国内可访问）翻译一段文本。

    附带 de= 邮箱参数，每日免费额度从 5 千字符提升到 5 万字符。
    注意：必须用 curl 发请求——实测同一 IP 下 Python urllib 的 TLS 指纹
    会被服务端持续限流（429），而 curl 完全正常（20 连发全部 200）。
    """
    import subprocess
    import urllib.parse

    url = ("https://api.mymemory.translated.net/get?q="
           + urllib.parse.quote(text) + f"&langpair={sl}|{tl}")
    cfg = load_email_config()
    if cfg and cfg.get("sender"):
        url += "&de=" + urllib.parse.quote(cfg["sender"])
    out = subprocess.run(
        ["curl", "-s", "-m", "30", "-w", "\n%{http_code}", url],
        capture_output=True, text=True, timeout=40,
    )
    if out.returncode != 0:
        raise RuntimeError(f"curl 退出码 {out.returncode}: {out.stderr[:100]}")
    body, _, code = out.stdout.rpartition("\n")
    if code != "200":
        raise RuntimeError(f"HTTP {code}（接口限流或异常）")
    data = json.loads(body)
    status = data.get("responseStatus")
    if status not in (200, "200"):
        raise RuntimeError(f"接口返回 {status}: {data.get('responseDetails', '')[:100]}")
    return data.get("responseData", {}).get("translatedText", "")


def _split_chunks(text, size=450):
    """按句子切分长文本，每段不超过 size 字符（接口限制 500）。"""
    parts = re.split(r"(?<=[.!?。！？;；\n])\s*", text)
    out, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) > size:
            out.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    return out or [text]


def translate_posts(posts, delay=0.8):
    """为每条推文生成互译：英文→中文，中文→英文，存入 text_translated 字段。

    已有译文的推文会自动跳过（支持断点续翻）；遇到 429 限流自动退避重试。
    """
    n, skipped, fail_streak = 0, 0, 0
    for p in posts:
        text = (p.get("text") or "").strip()
        if not text:
            p.setdefault("text_translated", "")
            p.setdefault("translated_to", "")
            continue
        if p.get("text_translated"):   # 已有译文，跳过
            skipped += 1
            n += 1
            continue
        if fail_streak >= 3:          # 连续失败 3 次：接口限流，快速跳过剩余
            p.setdefault("text_translated", "")
            p.setdefault("translated_to", "")
            continue
        has_cjk = bool(re.search(r"[\u4e00-\u9fff]", text))
        sl, tl = ("zh-CN", "en") if has_cjk else ("en", "zh-CN")
        ok = False
        for attempt in range(4):
            try:
                translated = " ".join(_translate_chunk(c, sl, tl) for c in _split_chunks(text))
                p["text_translated"] = translated.strip()
                p["translated_to"] = tl
                n += 1
                ok = True
                fail_streak = 0
                break
            except Exception as e:
                if "429" in str(e) and attempt < 3:
                    time.sleep(5 * (attempt + 1))  # 限流退避：5s/10s/15s
                    continue
                print(f"  ⚠ 翻译失败（{p.get('tweet_id', '?')}）：{e}")
                break
        if not ok:
            fail_streak += 1
            if fail_streak == 3:
                print("  ⚠ 连续 3 次翻译失败（接口限流），剩余推文跳过翻译，重跑即可补齐")
        time.sleep(delay if ok else 0.5)  # 控制请求节奏
    if skipped:
        print(f"（跳过已有译文 {skipped} 条）")
    print(f"翻译完成：{n}/{len(posts)} 条")
    return posts


# ======================== 图片下载与 HTML 报告 ========================

def download_images(posts):
    """把推文中的图片下载到 output/images/，并在每条推文中记录本地相对路径。"""
    import urllib.request

    img_dir = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(img_dir, exist_ok=True)
    total, ok = 0, 0
    for p in posts:
        local = []
        for i, url in enumerate(p.get("image_urls", []), 1):
            total += 1
            m = re.search(r"format=(\w+)", url)
            ext = "." + m.group(1) if m else ".jpg"
            fname = f"{p.get('tweet_id') or 'noid'}_{i}{ext}"
            fpath = os.path.join(img_dir, fname)
            if not os.path.exists(fpath):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as resp, open(fpath, "wb") as f:
                        f.write(resp.read())
                    ok += 1
                except Exception as e:
                    print(f"  ⚠ 图片下载失败 {url[:60]}...: {e}")
                    continue
            else:
                ok += 1
            local.append(f"images/{fname}")
        p["local_images"] = local
    print(f"图片下载完成：{ok}/{total} 张，保存在 {img_dir}")
    return posts


def generate_html_report(posts, target):
    """根据推文数据生成一个本地 HTML 报告。

    多个账号时左侧显示账号导航栏，正文按账号分组；单个账号时同样适用。
    """
    import html as _html

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(OUTPUT_DIR, f"{target}_report_{stamp}.html")

    def esc(s):
        return _html.escape(s or "")

    def linkify(s):
        """正文转义后，把 #话题 和 @用户 高亮。"""
        s = esc(s)
        s = re.sub(r"(#\w+)", r'<span class="tag">\1</span>', s)
        s = re.sub(r"(@[A-Za-z0-9_]{1,20})", r'<span class="mention">\1</span>', s)
        return s.replace("\n", "<br/>")

    def anchor_of(handle):
        return "acc-" + re.sub(r"[^A-Za-z0-9_]", "_", (handle or "unknown").lstrip("@"))

    def card_html(p):
        imgs = "".join(
            f'<a href="{esc(src)}" target="_blank"><img src="{esc(src)}" loading="lazy"/></a>'
            for src in p.get("local_images", [])
        )
        img_html = f'<div class="imgs n{min(len(p.get("local_images", [])), 4)}">{imgs}</div>' if imgs else ""
        badges = ("<span class=\"badge\">🔁 转发</span>" if p.get("is_retweet") else "") + \
                 ("<span class=\"badge\">📌 置顶</span>" if p.get("is_pinned") else "") + \
                 ("<span class=\"badge\">🎬 视频</span>" if p.get("has_video") else "")
        trans_html = ""
        if p.get("text_translated"):
            tlabel = "中文翻译" if p.get("translated_to") == "zh-CN" else "English"
            trans_html = (f'<div class="trans"><span class="tlabel">{tlabel}</span>'
                          f'{esc(p["text_translated"]).replace(chr(10), "<br/>")}</div>')
        return f"""
        <article class="card">
          <div class="head">
            <div class="avatar">{esc((p.get("author_name") or "?")[0])}</div>
            <div class="who">
              <div class="name">{esc(p.get("author_name"))} {badges}</div>
              <div class="meta">{esc(p.get("author_handle"))} · {esc(p.get("posted_at", "")[:16].replace("T", " "))} UTC</div>
            </div>
          </div>
          <div class="text">{linkify(p.get("text"))}</div>
          {trans_html}
          {img_html}
          <div class="foot">
            <span>💬 {p.get("reply_count", 0)}</span>
            <span>🔁 {p.get("retweet_count", 0)}</span>
            <span>❤️ {p.get("like_count", 0)}</span>
            <a href="{esc(p.get("url"))}" target="_blank">查看原文 ↗</a>
          </div>
        </article>"""

    # 按账号分组（保持抓取顺序），组内按时间倒序
    groups, order = {}, []
    for p in posts:
        h = p.get("author_handle") or "@unknown"
        if h not in groups:
            groups[h] = []
            order.append(h)
        groups[h].append(p)
    for h in order:
        groups[h].sort(key=lambda p: p.get("posted_at", ""), reverse=True)

    total_like = sum(p.get("like_count", 0) for p in posts)
    total_rt = sum(p.get("retweet_count", 0) for p in posts)
    total_reply = sum(p.get("reply_count", 0) for p in posts)
    total_img = sum(len(p.get("local_images", [])) for p in posts)
    multi = len(order) > 1
    title = "我的关注 · 推文报告" if multi else f"@{esc(target)} · 最新推文报告"

    # 侧边栏导航
    nav_items = "".join(
        f'<a href="#{anchor_of(h)}"><span class="nav-avatar">{esc((groups[h][0].get("author_name") or "?")[0])}</span>'
        f'<span class="nav-name">{esc(h)}</span><span class="nav-cnt">{len(groups[h])}</span></a>'
        for h in order
    )
    # 分组正文
    sections = ""
    for h in order:
        g = groups[h]
        g_like = sum(p.get("like_count", 0) for p in g)
        cards = "".join(card_html(p) for p in g)
        sections += f"""
        <section class="group" id="{anchor_of(h)}">
          <h2 class="gtitle">{esc(h)} <span>{len(g)} 条 · ❤️ {g_like}</span></h2>
          {cards}
        </section>"""

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>
  :root {{ --bg:#f5f8fa; --card:#fff; --ink:#0f1419; --sub:#536471; --blue:#1d9bf0; --line:#e6ecf0; }}
  * {{ box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }}
  .layout {{ display:flex; max-width:1020px; margin:0 auto; padding:24px 16px 60px; gap:22px; align-items:flex-start; }}
  aside.nav {{ position:sticky; top:20px; flex:none; width:230px; background:var(--card);
               border:1px solid var(--line); border-radius:14px; padding:14px 10px; }}
  aside.nav h3 {{ margin:4px 10px 10px; font-size:13px; color:var(--sub); letter-spacing:1px; }}
  aside.nav a {{ display:flex; align-items:center; gap:9px; padding:9px 10px; border-radius:10px;
                 text-decoration:none; color:var(--ink); font-size:14px; }}
  aside.nav a:hover {{ background:#eef6fd; }}
  .nav-avatar {{ width:30px; height:30px; border-radius:50%; background:var(--blue); color:#fff; flex:none;
                 display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; }}
  .nav-name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .nav-cnt {{ margin-left:auto; background:#e8f5fe; color:var(--blue); border-radius:10px;
              font-size:12px; padding:1px 8px; flex:none; }}
  main.content {{ flex:1; min-width:0; }}
  header.top {{ background:linear-gradient(135deg,#1d9bf0,#0b6bcb); color:#fff; border-radius:16px;
                padding:26px 24px; margin-bottom:16px; }}
  header.top h1 {{ margin:0 0 6px; font-size:22px; }}
  header.top .sub {{ opacity:.85; font-size:13px; }}
  .stats {{ display:flex; gap:10px; flex-wrap:wrap; margin:16px 0 22px; }}
  .stat {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
           padding:11px 16px; flex:1; min-width:100px; text-align:center; }}
  .stat b {{ display:block; font-size:19px; }}
  .stat span {{ color:var(--sub); font-size:12px; }}
  .gtitle {{ font-size:18px; margin:26px 4px 14px; padding-bottom:8px; border-bottom:2px solid var(--blue);
             scroll-margin-top:16px; }}
  .gtitle span {{ color:var(--sub); font-size:13px; font-weight:400; margin-left:8px; }}
  .group:first-of-type .gtitle {{ margin-top:4px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
           padding:18px 20px; margin-bottom:14px; }}
  .head {{ display:flex; gap:12px; align-items:center; margin-bottom:10px; }}
  .avatar {{ width:44px; height:44px; border-radius:50%; background:var(--blue); color:#fff;
             display:flex; align-items:center; justify-content:center; font-weight:700; font-size:18px; flex:none; }}
  .name {{ font-weight:700; }}
  .meta {{ color:var(--sub); font-size:13px; }}
  .badge {{ font-size:11px; background:#e8f5fe; color:var(--blue); border-radius:6px; padding:1px 6px; margin-left:4px; font-weight:400; }}
  .text {{ font-size:15px; line-height:1.6; white-space:normal; }}
  .tag, .mention {{ color:var(--blue); }}
  .trans {{ margin-top:12px; padding:11px 14px; background:#f0f7fd; border-left:3px solid var(--blue);
            border-radius:8px; font-size:14px; line-height:1.65; color:#33414e; }}
  .tlabel {{ display:inline-block; font-size:11px; color:#fff; background:var(--blue);
             border-radius:5px; padding:1px 7px; margin-right:6px; vertical-align:1px; }}
  .imgs {{ display:grid; gap:6px; margin-top:12px; }}
  .imgs.n1 {{ grid-template-columns:1fr; }}
  .imgs.n2, .imgs.n3, .imgs.n4 {{ grid-template-columns:1fr 1fr; }}
  .imgs img {{ width:100%; max-height:420px; object-fit:cover; border-radius:12px; border:1px solid var(--line); }}
  .foot {{ display:flex; gap:22px; align-items:center; margin-top:14px; color:var(--sub); font-size:14px; }}
  .foot a {{ margin-left:auto; color:var(--blue); text-decoration:none; }}
  .foot a:hover {{ text-decoration:underline; }}
  @media (max-width:760px) {{
    .layout {{ flex-direction:column; }}
    aside.nav {{ position:static; width:100%; display:flex; overflow-x:auto; gap:6px; }}
    aside.nav h3 {{ display:none; }}
    aside.nav a {{ flex:none; }}
  }}
</style>
</head>
<body>
<div class="layout">
  <aside class="nav"><h3>账号导航</h3>{nav_items}</aside>
  <main class="content">
    <header class="top">
      <h1>{title}</h1>
      <div class="sub">生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} · 数据来源：X (x.com) 实时抓取</div>
    </header>
    <div class="stats">
      <div class="stat"><b>{len(posts)}</b><span>推文数</span></div>
      <div class="stat"><b>{len(order)}</b><span>账号数</span></div>
      <div class="stat"><b>{total_like}</b><span>总点赞</span></div>
      <div class="stat"><b>{total_rt}</b><span>总转发</span></div>
      <div class="stat"><b>{total_reply}</b><span>总评论</span></div>
      <div class="stat"><b>{total_img}</b><span>图片数</span></div>
    </div>
    {sections}
  </main>
</div>
</body>
</html>"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return report_path


def _finish_posts(posts, target, args):
    """推文抓取后的统一收尾：下载图片 / 保存 / 生成报告 / 打印预览。"""
    if not posts:
        print("未抓取到任何推文。")
        return
    if getattr(args, "translate", False):
        translate_posts(posts)
    if args.images:
        download_images(posts)
    pj, pc = save_posts(posts, target)
    print(f"\n共抓取到 {len(posts)} 条推文，已保存到：")
    print(f"  JSON: {pj}")
    print(f"  CSV : {pc}")
    if args.report:
        rp = generate_html_report(posts, target)
        print(f"  HTML报告: {rp}")
        if load_email_config():
            send_report_email(rp, posts, target)
    print("\n推文预览（前 3 条）：")
    for t in posts[:3]:
        print(f"  - {t['author_handle']} [{t['posted_at'][:10]}] "
              f"❤{t['like_count']} 🔁{t['retweet_count']} 💬{t['reply_count']}")
        print(f"    {t['text'][:60]}")


def main():
    parser = argparse.ArgumentParser(description="抓取 X 账户关注列表中的用户信息及最近推文，并保存到本地")
    parser.add_argument("--user", default="",
                        help="要抓取的单个目标账号（如 ScienceMagazine）；不填则优先使用 --accounts-file 清单")
    parser.add_argument("--accounts-file", default=os.path.join(BASE_DIR, "accounts.txt"),
                        help="账号清单 txt 文件（每行一个账号），存在且未指定 --user 时自动启用")
    parser.add_argument("--days", type=int, default=7,
                        help="只收集最近 N 天发表的推文（默认 7 天）")
    parser.add_argument("--incremental", action="store_true",
                        help="增量模式：只抓上次运行后新发表的推文（状态存于 output/state.json）")
    parser.add_argument("--max", type=int, default=200,
                        help="最多抓取的关注用户数量，0 表示不限制（默认 200）")
    parser.add_argument("--posts", type=int, default=0,
                        help="抓取推文的数量；self 模式下默认 20，following 模式下默认 0（不抓）")
    parser.add_argument("--posts-users", type=int, default=5,
                        help="following 模式下只对前 N 个关注用户抓推文（默认 5）")
    parser.add_argument("--posts-scope", choices=["following", "self"], default="following",
                        help="推文抓取对象：following=被关注的人（默认），self=目标账号自己")
    parser.add_argument("--images", dest="images", action="store_true", default=True,
                        help="下载推文中的图片到本地 output/images/（默认开启）")
    parser.add_argument("--no-images", dest="images", action="store_false",
                        help="不下载图片")
    parser.add_argument("--report", dest="report", action="store_true", default=True,
                        help="生成 HTML 报告并发送邮件（默认开启）")
    parser.add_argument("--no-report", dest="report", action="store_false",
                        help="不生成报告、不发邮件")
    parser.add_argument("--translate", dest="translate", action="store_true", default=True,
                        help="为推文生成中英互译（英文→中文，中文→英文），并写入报告（默认开启）")
    parser.add_argument("--no-translate", dest="translate", action="store_false",
                        help="不做翻译")
    parser.add_argument("--keep-open", action="store_true",
                        help="抓取完成后不关闭浏览器")
    args = parser.parse_args()

    driver = build_driver()
    try:
        driver.get("https://x.com/home")
        try:
            wait_for_login(driver)
        except Exception:
            print("等待登录超时，请重新运行脚本并尽快完成登录。")
            return

        username = get_my_username(driver)
        if not username:
            print("无法获取当前登录用户名，请确认已登录后重试。")
            return
        print(f"当前登录账户：@{username}")

        # 模式零：账号清单文件模式（未指定 --user 且清单文件存在时自动启用）
        if not args.user and os.path.exists(args.accounts_file):
            accounts = load_accounts(args.accounts_file)
            if not accounts:
                print(f"账号清单 {args.accounts_file} 为空，请在文件中每行填写一个账号。")
                return
            n = args.posts if args.posts > 0 else 30
            state = load_state() if args.incremental else {"accounts": {}}
            mode_txt = "增量检测新推文" if args.incremental else f"抓取最近 {args.days} 天的推文"
            print(f"从 {os.path.basename(args.accounts_file)} 读取到 {len(accounts)} 个账号，"
                  f"{mode_txt}（每账号最多 {n} 条）")
            all_posts = []
            per_account = {}
            for i, acc in enumerate(accounts, 1):
                print(f"\n[{i}/{len(accounts)}] @{acc}")
                since_id = state["accounts"].get(acc, {}).get("last_id") if args.incremental else None
                posts = scrape_recent_posts(driver, acc, n, since_days=args.days, since_id=since_id)
                per_account[acc] = len(posts)
                if args.incremental:
                    ids = [int(p["tweet_id"]) for p in posts if p["tweet_id"].isdigit()]
                    old_max = int(since_id) if since_id else 0
                    new_max = max(ids + [old_max])
                    state["accounts"][acc] = {
                        "last_id": str(new_max),
                        "last_run": datetime.now(timezone.utc).isoformat(),
                    }
                all_posts.extend(posts)
                time.sleep(2)

            if args.incremental:
                save_state(state)
                if not all_posts:
                    print("\n✅ 增量检测完成：所有账号均无新推文，无需保存。")
                    return
                print(f"\n检测到 {len(all_posts)} 条新推文：{per_account}")
                notify_macos("X 推文更新", f"{len(all_posts)} 条新推文已保存到本地")
            _finish_posts(all_posts, "my_accounts", args)
            return

        target = args.user.lstrip("@") if args.user else username
        print(f"抓取目标账号：@{target}")

        # 模式一：直接抓取目标账号自己最新发表的推文
        if args.posts_scope == "self":
            n = args.posts if args.posts > 0 else 20
            posts = scrape_recent_posts(driver, target, n, since_days=args.days)
            _finish_posts(posts, target, args)
            return

        # 模式二：抓取目标账号的关注列表（可选再抓被关注者的推文）
        users = scrape_following(driver, target, args.max)
        print(f"\n共抓取到 {len(users)} 个关注的用户。")

        if users:
            json_path, csv_path = save_results(users, target)
            print("结果已保存到：")
            print(f"  JSON: {json_path}")
            print(f"  CSV : {csv_path}")
            print("\n前 5 个用户预览：")
            for u in users[:5]:
                mark = "✔" if u["verified"] else " "
                print(f"  {mark} {u['name']} ({u['handle']}) - {u['bio'][:40]}")
        else:
            print("未抓取到任何用户，可能是页面结构变化或网络问题。")

        if args.posts > 0 and users:
            targets = users[:args.posts_users]
            print(f"\n开始抓取前 {len(targets)} 个用户最近 {args.posts} 条推文...")
            all_posts = []
            for i, u in enumerate(targets, 1):
                print(f"[{i}/{len(targets)}] {u['name']} ({u['handle']})")
                all_posts.extend(scrape_recent_posts(driver, u["handle"], args.posts))
                time.sleep(2)  # 控制节奏，降低被限制的风险
            _finish_posts(all_posts, target, args)
    finally:
        if not args.keep_open:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
