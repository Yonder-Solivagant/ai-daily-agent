"""
作业 2 主入口：一次完整跑通「拉 RSS → 盘家底 → 分析 → 发邮件」。
用 Windows 任务计划程序每天定时调用本文件即可（见 README）。

日志：每次运行落一份 logs/run_YYYY-MM-DD_HHMMSS.log，便于事后核对「到点真跑了」。
"""
import sys
import traceback
from datetime import datetime
from rss_watch import pull_new
from inventory import scan, to_markdown
from analyze import build_report
from mailer import send_robust
from config import LOG_DIR

import os


def _log(msg):
    print(msg, flush=True)


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"run_{datetime.now():%Y-%m-%d_%H%M%S}.log")
    lines = []

    def emit(msg):
        lines.append(msg)
        _log(msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    emit(f"=== 定时机器启动 {datetime.now():%Y-%m-%d %H:%M:%S} ===")
    try:
        new_items = pull_new()
        emit(f"[步骤1] 外部输入：新增资讯 {len(new_items)} 条")

        inv_md = to_markdown(scan())
        inv_path = os.path.join(LOG_DIR, "家底地图_latest.md")
        with open(inv_path, "w", encoding="utf-8") as f:
            f.write(inv_md)
        emit(f"[步骤2] 本机家底：{inv_md.splitlines()[2][:80]}")

        report = build_report(new_items, inv_md)
        emit("[步骤3] 分析完成，日报正文 %d 字" % len(report))

        subject = f"AI 日报 {datetime.now():%Y-%m-%d}"
        sent = send_robust(subject, report)
        emit(f"[步骤4] 邮件{'已发出' if sent else '未发送（未配 SMTP）'}")
        emit("=== 完成 ===")
        return 0
    except Exception:
        emit("!!! 运行失败 !!!\n" + traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
