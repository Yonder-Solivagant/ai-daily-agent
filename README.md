# 定期开工的机器（作业 2）

给这台电脑装一条**到点自己开工**的流水线：**拉外部资讯 → 盘本机家底 → 大模型出日报 → 发到自己邮箱**。
Windows 任务计划程序每天 08:00 自动拉起，人不参与。

## 链路

```
① 外部输入   rss_watch.py    橘鸦AI早报 / Hugging Face Blog（state.json 去重，新条目落 store/）
② 盘本机家底  inventory.py    遍历本机目录 → 「数据/代码技能/文档」家底地图（分类+体量）
③ 分析      analyze.py      新资讯 + 家底 → DeepSeek 出日报（3 条要点 + 结合点 + 建议）
④ 送达      mailer.py       SMTP 发到自己邮箱；tools/imap_check.py 可回读自证
```

- 主入口：`run_once.py`（一次跑完整条链）
- 定时入口：`run_task.cmd`（被任务计划程序拉起，输出追加到 `logs/task_console.log`）
- 录屏面板：`tools/record_demo.py`（GUI 面板，把全过程实时显示出来，用于录屏）

## 快速开始

```powershell
cd Repository\ai-daily-agent
uv venv --python 3.14 .venv                 # 或 python -m venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
copy .env.example .env                      # 填 LLM_KEY / SMTP_* / PROXY
.venv\Scripts\python.exe run_once.py        # 手动跑一次
```

不填 `LLM_KEY` 也能跑（日报退化为纯汇编）；不填 SMTP 则只打印不发信。

## 装上定时（真正「定期开工」）

```powershell
$dir = "E:\Work\Master\人工智能与数据分析\Repository\ai-daily-agent"
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c ""' + $dir + '\run_task.cmd""') -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -Daily -At '08:00'
Register-ScheduledTask -TaskName 'AI日报机器' -Action $action -Trigger $trigger `
  -Description '作业2：每天 08:00 自动拉起 AI 日报机器' -Force
```

查状态 / 手动触发（录屏演示就是用手动触发，与到点自动触发同一条路径）：

```powershell
schtasks /query /tn "AI日报机器" /fo LIST /v
schtasks /run   /tn "AI日报机器"
Get-Content logs\task_console.log -Wait      # 实时看任务在干什么
```

## 录屏（作业2 的交付物）

`tools/record_demo.py` 是为录屏写的 GUI 面板：依次展示「已注册的定时任务 → 手动触发 → 控制台日志实时滚动 → 任务结果 → 用 IMAP 回读邮箱里那封日报」。

```powershell
# 1) 起面板（pythonw 不带控制台窗口）
.venv\Scripts\pythonw.exe tools\record_demo.py --flag logs\demo_done.flag
# 2) 用 ffmpeg 只录这个窗口（标题 AI-Daily-Machine Job2 Demo）
ffmpeg -y -f gdigrab -framerate 12 -i title="AI-Daily-Machine Job2 Demo" -t 600 ^
       -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p 交付物\作业2_录屏.mp4
```

产物在 `交付物/作业2_录屏.mp4`（约 2 分钟，2560×1400）。

## 环境变量（.env）

| 变量 | 作用 |
|---|---|
| `LLM_BASE` / `LLM_KEY` / `LLM_MODEL` | 日报生成（DeepSeek，OpenAI 兼容） |
| `SMTP_HOST/PORT/USER/PASS` / `MAIL_TO` | 发信（QQ 邮箱 SSL 465，`PASS` 填**授权码**） |
| `PROXY` | 部分 RSS 直连不通时走本机代理（如 `http://127.0.0.1:8888`），留空=直连 |
| `MAX_ITEMS_PER_FEED` | 每个源单次最多取几条（默认 15） |

## 两个坑（都已在代码里处理）

1. **HTTPS 证书**：本机 Clash Verge 会做 HTTPS 解密，它的自签根证书装在 **Windows 系统证书库**里；
   Python 默认不认系统库 → `CERTIFICATE_VERIFY_FAILED`。解法不是关校验，而是装 `truststore` 并注入 ssl
   （`net.py`），让 Python 按系统库校验。
2. **.cmd 编码**：`cmd.exe` 按系统 ANSI 代码页读 `.cmd`，文件里有中文注释会整行乱码导致任务 `9009`。
   `run_task.cmd` 全 ASCII，中文说明放 README。

## 目录

```
config.py      配置（RSS 源 / 扫描根目录 / LLM / SMTP / 代理）
net.py         统一网络层：truststore + 直连→代理两级降级
rss_watch.py   ① 外部输入（去重 + 落盘 store/）
inventory.py   ② 盘本机家底（分类清单 + 体量统计）
analyze.py     ③ 大模型出日报（失败自动退化为纯汇编）
mailer.py      ④ 发信（465 SSL，失败退回 587 STARTTLS）
run_once.py    主入口（一次跑完整条链，写 logs/run_*.log）
run_task.cmd   定时入口（任务计划程序调用，控制台输出进 logs/task_console.log）
tools/imap_check.py     回读邮箱最新一封日报（收信自证）
tools/record_demo.py    录屏用 GUI 演示面板
交付物/作业2_录屏.mp4    录屏成片
```

## 安全

- `.env` / `state.json` / `store/` / `logs/` / `.venv/` / `交付物/` 均已在 `.gitignore`，仓库与录屏里不出现密钥。
- 邮箱用授权码而非登录密码；LLM key 只在 `.env` 与环境变量里。
