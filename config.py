"""
作业 2 · 定期开工的机器 —— 配置
三件事：① 接外部输入（AI RSS）② 盘本机家底 ③ 定时分析并发邮件。
所有密钥走环境变量（见 .env.example），不要写进仓库。
"""
import os
from dotenv import load_dotenv

# 以本文件所在目录为基准找 .env，保证被任务计划程序从任意工作目录调用时也能读到
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ---- 网络代理 ----
# 部分 RSS 源直连不通，需要走本机代理（例：127.0.0.1:8888）。留空 = 直连。
PROXY = os.environ.get("PROXY", "")

# ---- ① 外部输入：AI 相关 RSS ----
# 橘鸦AI早报 已核实可用（2026-10-01 实测）；其余为常见公开源，首次运行请自查可用。
FEEDS = [
    {"name": "橘鸦AI早报", "url": "https://daily.juya.uk/rss.xml"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    # 如需中文源，自查后取消注释：
    # {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
    # {"name": "量子位", "url": "https://www.qbitai.com/feed"},
]

# 每个源单次最多取多少条（有些源是全量归档，不限量会一次拉几百条）
MAX_ITEMS_PER_FEED = int(os.environ.get("MAX_ITEMS_PER_FEED", "15"))

# ---- ② 本机家底扫描根目录（按需改成本机真实路径）----
SCAN_ROOTS = [
    r"E:\Work\Master\人工智能与数据分析",
    r"E:\Work\AI",
]
# 扫描时忽略的目录
IGNORE_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".context", ".temp", ".vercel"}

# ---- ③ 分析与邮件 ----
LLM_BASE = os.environ.get("LLM_BASE", "https://api.deepseek.com")
LLM_KEY = os.environ.get("LLM_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
MAIL_TO = os.environ.get("MAIL_TO", "")

# 状态/落盘
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")
STORE_DIR = os.path.join(BASE_DIR, "store")   # 新抓取的文章存这里
LOG_DIR = os.path.join(BASE_DIR, "logs")      # 每次运行的日志（作业2 录屏/留痕用）
