# Windows 安装说明 · X (Twitter) 推文抓取工具

> 适用系统：Windows 10 / 11
> 目标：在一台新 Windows 电脑上从零装好本工具，约 15 分钟。

---

## 一、需要准备什么

| 项目 | 说明 |
|------|------|
| Python 3.10+ | 官网安装，**务必勾选 "Add python.exe to PATH"** 和 "py launcher" |
| Google Chrome | 正常安装的桌面版 Chrome（脚本会自动找到 `C:\Program Files\Google\Chrome\Application\chrome.exe`） |
| 本项目文件夹 | 整个 `twitter` 文件夹拷过来即可（含 `drivers/`、`chrome_profile_x/` 更好，可省掉重新登录） |

---

## 二、安装步骤（5 步）

### 第 1 步：放置项目

把整个 `twitter` 文件夹复制到固定位置，例如：

```
C:\Users\你的用户名\Desktop\twitter\twitter
```

> 路径一旦确定就不要再移动，否则定时任务要重建。

### 第 2 步：安装 Python 依赖

打开"命令提示符"（CMD），执行：

```bat
py -3 -m pip install selenium requests
```

> 验证：`py -3 -c "import selenium; print(selenium.__version__)"` 能输出版本号即成功。
> 本机当前版本：Python 3.14.0 + selenium 4.43.0（仅供参考，更高版本一般也兼容）。

### 第 3 步：准备 ChromeDriver（关键）

`drivers\chromedriver.exe` 的版本**必须与本机 Chrome 大版本一致**。

1. 查看本机 Chrome 版本：打开 Chrome → 菜单 → 帮助 → 关于 Google Chrome（如 `149.x.x.x`）。
2. 如果 `drivers\chromedriver.exe` 大版本不一致（运行 `drivers\chromedriver.exe --version` 查看），
   到 npmmirror 镜像下载同大版本：
   `https://registry.npmmirror.com/-/binary/chrome-for-testing/`
   → 选对应大版本目录 → `win64` → 下载 `chromedriver-win64.zip` → 解压出 `chromedriver.exe` 覆盖到 `drivers\`。

### 第 4 步：配置邮箱（可选，不配置则不发邮件）

在项目目录新建 `email_config.json`：

```json
{
  "smtp_host": "smtp.qq.com",
  "smtp_port": 465,
  "sender": "你的QQ号@qq.com",
  "auth_code": "QQ邮箱SMTP授权码",
  "recipient": "收件邮箱@qq.com"
}
```

> QQ 邮箱授权码获取：网页登录 QQ 邮箱 → 设置 → 账号 → 开启 SMTP 服务 → 生成授权码（**不是 QQ 密码**）。
> 此文件含密钥，勿外传；删除该文件即停用邮件功能。

### 第 5 步：首次运行 + 登录 X

```bat
cd /d C:\Users\你的用户名\Desktop\twitter\twitter
py -3 01_x_following_scraper.py --user @dotey --posts-scope self --days 1 --posts 5
```

- 会弹出 Chrome 窗口，**手动登录一次 X 账号**（登录态保存在 `chrome_profile_x\`，以后无需再登录）。
- 如果项目里已带有旧机器的 `chrome_profile_x\` 文件夹，可能直接免登录。
- 成功标志：控制台显示抓到推文、生成 JSON/CSV/HTML 报告、（配置了邮箱时）提示邮件已发送。

---

## 三、脚本说明（每个文件干什么）

| 文件 | 作用 |
|------|------|
| `01_x_following_scraper.py` | **主程序**。打开 Chrome → 抓推文（默认读 `accounts.txt` 抓最近 7 天）→ 翻译（MyMemory 免费接口）→ 下载图片 → 生成 HTML 报告 → 发邮件 |
| `02_test_scraper.py` | 自动化测试脚本（59 项检查），维护时用：`py -3 02_test_scraper.py` |
| `03_auto_scrape.bat` | **Windows 自动任务入口**（定时任务调用的就是它）。带目录锁防重复运行，执行 `01 --incremental --translate --images --report`，日志写入 `logs\auto_scrape.log` |
| `03_auto_scrape.sh` | macOS 版自动任务入口（Windows 上不用） |
| `com.kimi.xscraper.plist` | macOS launchd 配置（Windows 上不用） |
| `04_backfill_translate.py` | 补翻译工具：`py -3 04_backfill_translate.py output\xxx.json`，给没译完的 JSON 补译并重生成报告 |
| `accounts.txt` | 关注账号清单，每行一个，`#` 开头为注释。日常维护只改这个文件 |
| `email_config.json` | 邮箱配置（见第 4 步） |
| `drivers\chromedriver.exe` | Chrome 驱动（见第 3 步） |
| `chrome_profile_x\` | Chrome 用户数据（保存 X 登录态），**勿删**，删了要重新登录 |
| `output\` | 抓取结果：`*.json / *.csv / *_report_*.html / images\ / state.json`（增量状态，勿删） |
| `logs\` | 自动任务日志 |

---

## 四、配置定时任务（每 2 小时自动增量检查）

以**管理员身份**打开 CMD，执行（路径换成你的实际路径）：

```bat
schtasks /Create /TN "XScraper" /TR "C:\Users\你的用户名\Desktop\twitter\twitter\03_auto_scrape.bat" /SC DAILY /ST 09:32 /RI 120 /F
```

- `/SC DAILY /ST 09:32`：每天 9:32 首次触发；`/RI 120`：之后每 120 分钟重复一次。
- 行为：只抓**没发送过的新推文**（状态记在 `output\state.json`）；无新内容则静默结束不发邮件。

管理命令：

```bat
schtasks /Query /TN "XScraper" /V /FO LIST    :: 查看状态
schtasks /Run /TN "XScraper"                  :: 立即手动触发一次
schtasks /End /TN "XScraper"                  :: 停止正在运行的本次任务
schtasks /Delete /TN "XScraper" /F            :: 删除任务（停用自动化）
```

> 手动执行一次同样的自动检查：直接双击 `03_auto_scrape.bat`。

---

## 五、日常使用速查

```bat
cd /d C:\Users\你的用户名\Desktop\twitter\twitter

:: 抓清单里所有账号最近 7 天推文（翻译+图片+报告+邮件，默认全开）
py -3 01_x_following_scraper.py

:: 只抓新推文（增量，等同自动任务）
py -3 01_x_following_scraper.py --incremental

:: 抓单个账号
py -3 01_x_following_scraper.py --user elonmusk --posts-scope self --posts 30

:: 只要数据，不翻译不发邮件
py -3 01_x_following_scraper.py --no-translate --no-report
```

---

## 六、常见问题

1. **提示等待登录超时**：10 分钟内没在弹出的 Chrome 里完成登录，重新运行即可。
2. **登录态失效**：删除 `chrome_profile_x\` 文件夹后重新运行并登录。
3. **报 ChromeDriver 版本错误**：按第 3 步重新下载匹配版本的驱动。
4. **部分推文没译文**：免费翻译接口每日 5 万字符额度，隔天自动补齐，或用 `04_backfill_translate.py` 手动补。
5. **定时任务没动静**：`schtasks /Query /TN "XScraper" /V /FO LIST` 查状态，看 `logs\auto_scrape.log` 排查。
6. **项目移动了位置**：删旧任务、用新路径重建定时任务（第 4 步）。
