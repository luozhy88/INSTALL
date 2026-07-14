# X (Twitter) 推文抓取工具 · 使用说明

自动打开 Chrome 浏览器，抓取指定账号最新发表的推文，支持**完整正文、中英互译、
图片下载**，并生成**带侧边栏导航的本地 HTML 报告**。支持**增量检测**与
**开机/每 3 天自动运行**。

> 项目位置：`~/kimi/twitter`（即 `/Users/apple/kimi/twitter`，已避开桌面隐私限制）

---

## 一、日常使用（最常用）

```bash
cd ~/kimi/twitter
python3 01_x_following_scraper.py
```

不加 `--user` 时，程序自动读取 `accounts.txt` 里的账号清单，
逐个抓取**最近 7 天**发表的推文（每账号最多 30 条），然后：
翻译 → 下载图片 → 保存 JSON/CSV → 生成 HTML 报告 → 发送邮件。
（翻译/图片/报告/邮件**默认全部开启**，可用 `--no-translate` / `--no-images` / `--no-report` 关闭）

> 首次使用会弹出 Chrome 窗口，手动登录一次 X 账号即可，
> 登录状态保存在 `chrome_profile_x/`，以后无需再登录。

---

## 二、自动化（Windows 任务计划程序，已配置好，无需操作）

Windows 任务计划程序任务 `XScraper` 已启用：**每 2 小时自动运行一次**增量检查（机器常开，无需开机/唤醒补跑逻辑）。

- **增量检测**：只抓最近 7 天中**尚未发送过**的新推文（状态记录在 `output/state.json`）；无新内容则静默结束、不发邮件；有新内容才抓图/生成报告/**发送邮件**
- **自动流程包含翻译**（MyMemory 免费接口，经 curl 调用；每日 5 万字符额度，增量运行远低于上限）
- **防重复运行**：目录锁 `.scrape.lock`，上一次未结束时本次自动跳过
- **运行日志**：`logs/auto_scrape.log`

手动执行一次自动检查：双击 `03_auto_scrape.bat`，或：

```bat
03_auto_scrape.bat
```

管理定时任务：

```bat
schtasks /query /tn "XScraper" /v /fo list        :: 查看状态
schtasks /end /tn "XScraper"                      :: 停止本次运行
schtasks /delete /tn "XScraper" /f                :: 删除任务（停用）
```

> 说明：macOS 版的 `03_auto_scrape.sh` + `com.kimi.xscraper.plist`（launchd）仍保留，
> 在 Mac 上使用时参考旧版说明即可。

---

## 三、邮件报告（已配置）

每次生成 HTML 报告后（手动运行或定时任务），报告会**自动发送到 `479321347@qq.com`**：

- **报告以附件形式发送**：附件是"自包含"HTML——所有图片已用 base64 嵌入文件内部，
  下载后双击即可在浏览器中查看完整报告（侧边栏导航、中英互译、高清图片），单个文件无需联网
- 邮件正文附带摘要：各账号推文数统计 + 点赞 Top 5 速览
- 配置文件：`email_config.json`（600 权限，含 SMTP 授权码，**勿外传**）
- 想停用邮件：删除或重命名 `email_config.json` 即可；改收件人：编辑其中的 `recipient`

---

## 四、维护关注清单 `accounts.txt`

```text
# 每行一个账号，@ 可写可不写；# 开头是注释
@TrumpDailyPosts
@fatwang2ai
@tangming2005
@EricTopol
```

想增减关注对象，直接编辑这个文件即可，下次运行（手动或自动）自动生效。

---

## 五、常用命令一览

| 需求 | 命令 |
|------|------|
| 抓清单里所有人最近 7 天推文（翻译+图片+报告+邮件，默认全开） | `python3 01_x_following_scraper.py` |
| 只抓新推文（增量，等同自动任务） | 加 `--incremental` |
| 改时间范围为最近 3 天 | 加 `--days 3` |
| 抓单个账号（不用清单） | `python3 01_x_following_scraper.py --user Nature --posts-scope self --posts 30` |
| 只要数据，不翻译/不发邮件 | 加 `--no-translate --no-report` |
| 抓某账号的关注列表 | `python3 01_x_following_scraper.py --user ScienceMagazine --max 50` |
| 抓关注列表 + 被关注者的推文 | 加 `--posts 10 --posts-users 5` |
| 抓完不关闭浏览器 | 加 `--keep-open` |

完整参数：`python3 01_x_following_scraper.py --help`

---

## 六、输出产物（在 `output/` 目录）

| 文件 | 说明 |
|------|------|
| `my_accounts_report_时间戳.html` | **HTML 报告**：左侧账号导航栏，按人分组，原文+译文+图片+互动数据，双击即可打开 |
| `my_accounts_recent_posts_时间戳.json` | 结构化数据（含全部字段） |
| `my_accounts_recent_posts_时间戳.csv` | Excel 可直接打开（UTF-8 BOM，中文不乱码） |
| `images/` | 推文原图（large 高清版）。报告通过相对路径引用，**移动报告时请连同 images 文件夹一起移动** |
| `state.json` | 增量抓取状态（每账号上次最新推文 ID），**勿删**，删了会重抓 |

---

## 七、常见问题

1. **提示"等待登录超时"**：运行后未在 10 分钟内完成登录。重新运行，在弹出的 Chrome 窗口登录即可。
2. **登录态失效**：删除 `chrome_profile_x/` 文件夹后重新运行并登录。
3. **部分推文没有译文**：免费翻译接口（MyMemory）有每日额度限制（带邮箱参数 5 万字符/天）。
   脚本已内置限流退避重试与断点续翻，隔一段时间重跑一次即可补齐（已翻译的自动跳过）；
   也可运行 `python3 04_backfill_translate.py output/xxx.json` 单独补译并重新生成报告。
   日常增量运行条数少，一般不会触发。
4. **Chrome 升级后报错**：删除 `drivers/chromedriver.exe`，从 npmmirror 镜像按本机 Chrome 版本重新下载（如 `https://registry.npmmirror.com/-/binary/chrome-for-testing/` 下选同一大版本），解压到 `drivers/`。
5. **某个账号没抓到推文**：该账号可能近 7 天未发推，或主页受保护/被限制。
6. **自动任务没有运行**：`launchctl list | grep xscraper` 查看是否已加载；查看 `logs/launchd.err.log` 排查。

---

## 八、目录结构

```
~/kimi/twitter/
├── 01_x_following_scraper.py   # 主程序（Windows/macOS 通用）
├── 02_test_scraper.py          # 自动化测试（59 项）
├── 03_auto_scrape.bat          # Windows 自动增量抓取入口（任务计划程序调用）
├── 03_auto_scrape.sh           # macOS 自动增量抓取入口（launchd 调用）
├── com.kimi.xscraper.plist     # macOS launchd 配置
├── accounts.txt                # 关注账号清单（按需要编辑）
├── email_config.json           # 邮箱配置（SMTP 授权码，勿外传）
├── tests/                      # 测试用模拟页面
├── drivers/chromedriver.exe    # Windows 驱动（与本机 Chrome 匹配）
├── drivers/chromedriver        # macOS 驱动
├── chrome_profile_x/           # 浏览器配置（保存登录状态，勿删）
├── logs/                       # 自动任务日志
└── output/                     # 抓取结果（JSON/CSV/HTML/images/state.json）
```
