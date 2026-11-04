"""作业2 · 录屏演示面板（GUI）。

自己开一个窗口，把「定时任务 → 被拉起 → 跑完 → 邮箱收到日报」全过程实时显示出来，
比裸终端更适合录屏：字号大、只占一个窗口、录制时不会被别的窗口盖住。

用法（用 pythonw 启动，避免带出控制台窗口）：
    .venv\\Scripts\\pythonw.exe tools\\record_demo.py --flag logs\\demo_done.flag
"""
import argparse
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK = "AI日报机器"
LOG = os.path.join(BASE, "logs", "task_console.log")
MAIL = os.path.join(BASE, "logs", "latest_mail.txt")
TITLE = "AI-Daily-Machine Job2 Demo"

BG = "#0f1419"
FG = "#d7dde3"
ACCENT = "#4ea1ff"
OK = "#5ac18e"
WARN = "#e6b450"


def run_cmd(args):
    try:
        p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        return (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return f"[命令失败] {e}"


class Panel:
    def __init__(self, root, flag_path):
        self.root = root
        self.flag_path = flag_path
        self.q = queue.Queue()
        self.root.title(TITLE)
        self.root.configure(bg=BG)
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)   # per-monitor aware，避免缩放黑边
        except Exception:
            pass
        self.root.geometry("2560x1400+0+0")
        self.root.attributes("-topmost", True)

        self.f_title = tkfont.Font(family="Microsoft YaHei UI", size=19, weight="bold")
        self.f_head = tkfont.Font(family="Microsoft YaHei UI", size=13, weight="bold")
        self.f_body = tkfont.Font(family="Microsoft YaHei UI", size=12)
        self.f_mono = tkfont.Font(family="Consolas", size=12)
        self.f_small = tkfont.Font(family="Microsoft YaHei UI", size=10)

        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=26, pady=(22, 6))
        tk.Label(top, text="作业 2 · 定期开工的机器", font=self.f_title, fg=FG, bg=BG).pack(side="left")
        tk.Label(top, text="定时任务 → 被拉起 → 自动分析 → 结果发邮箱", font=self.f_body, fg=ACCENT, bg=BG).pack(side="left", padx=16)
        self.clock = tk.Label(top, text="", font=self.f_small, fg="#7f8c99", bg=BG)
        self.clock.pack(side="right")

        self.text = tk.Text(root, font=self.f_mono, bg=BG, fg=FG, wrap="none",
                            bd=0, padx=26, pady=8, insertbackground=FG, height=40)
        self.text.pack(fill="both", expand=True)
        self.text.tag_configure("head", font=self.f_head, foreground=ACCENT, spacing1=14, spacing3=6)
        self.text.tag_configure("body", font=self.f_body, foreground=FG, spacing1=2)
        self.text.tag_configure("mono", font=self.f_mono, foreground="#c9d1d9")
        self.text.tag_configure("ok", font=self.f_mono, foreground=OK)
        self.text.tag_configure("warn", font=self.f_mono, foreground=WARN)
        self.text.tag_configure("dim", font=self.f_small, foreground="#7f8c99")
        self.text.configure(state="disabled")

        self.root.after(100, self._drain)
        self.root.after(1000, self._tick_clock)
        threading.Thread(target=self._worker, daemon=True).start()

    # ---------- UI ----------
    def _tick_clock(self):
        self.clock.configure(text=f"本机时间 {time.strftime('%Y-%m-%d %H:%M:%S')}    ·    Windows 任务计划程序")
        self.root.after(1000, self._tick_clock)

    def put(self, text="", tag="mono"):
        self.q.put((text, tag))

    def _drain(self):
        try:
            while True:
                text, tag = self.q.get_nowait()
                self.text.configure(state="normal")
                self.text.insert("end", text + "\n", tag)
                self.text.see("end")
                self.text.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(150, self._drain)

    # ---------- 演示流程 ----------
    def _worker(self):
        self.put("=== 作业2 · 定期开工的机器 —— 定时任务演示 ===", "head")
        self.put(f"开始时间：{time.strftime('%Y-%m-%d %H:%M:%S')}", "dim")

        self.put("\n【1】已注册的定时任务（Windows 任务计划程序，每天 08:00 自动拉起，无需人管）", "head")
        out = run_cmd(["schtasks", "/query", "/tn", TASK, "/fo", "LIST", "/v"])
        for line in out.splitlines():
            s = line.strip()
            if any(k in s for k in ("Next Run Time", "Last Run Time", "Last Result", "Task To Run", "Status")):
                self.put("    " + s, "mono")
        time.sleep(4)

        self.put("\n【2】现在手动触发一次（与到点自动触发完全同一条路径）", "head")
        out = run_cmd(["schtasks", "/run", "/tn", TASK])
        for line in out.splitlines():
            if line.strip():
                self.put("    " + line.strip(), "ok")
        time.sleep(3)

        self.put("\n【3】任务已被任务计划程序拉起，控制台日志实时滚动", "head")
        seen = 0
        deadline = time.time() + 420
        done = False
        while time.time() < deadline and not done:
            if os.path.exists(LOG):
                try:
                    lines = open(LOG, encoding="utf-8", errors="replace").read().splitlines()
                except Exception:
                    lines = []
                if len(lines) > seen:
                    for ln in lines[seen:]:
                        tag = "ok" if ("邮件已发出" in ln or "完成" in ln or "exit code 0" in ln) else "mono"
                        self.put("    " + ln, tag)
                    seen = len(lines)
                if any("task finished" in l for l in lines):
                    done = True
            time.sleep(1.5)
        time.sleep(2)

        self.put("\n【4】任务运行结果（任务计划程序记录）", "head")
        out = run_cmd(["schtasks", "/query", "/tn", TASK, "/fo", "LIST", "/v"])
        for line in out.splitlines():
            s = line.strip()
            if any(k in s for k in ("Last Run Time", "Last Result", "Next Run Time")):
                self.put("    " + s, "mono")
        time.sleep(2)

        self.put("\n【5】用 IMAP 回读自己邮箱里收到的这封日报（收信自证）", "head")
        out = run_cmd([os.path.join(BASE, ".venv", "Scripts", "python.exe"),
                       os.path.join(BASE, "tools", "imap_check.py")])
        for line in out.splitlines():
            if line.strip():
                self.put("    " + line.strip(), "ok")
        if os.path.exists(MAIL):
            time.sleep(1)
            body = open(MAIL, encoding="utf-8", errors="replace").read().splitlines()
            self.put("", "body")
            for ln in body[:34]:
                self.put("    " + ln, "body")
        time.sleep(3)

        self.put("\n=== 演示结束：定时任务已就位，每天 08:00 自动开工并把日报发到邮箱 ===", "head")
        try:
            with open(self.flag_path, "w", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception:
            pass
        time.sleep(6)
        self.root.after(0, self.root.destroy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flag", default=os.path.join(BASE, "logs", "demo_done.flag"))
    args = ap.parse_args()
    root = tk.Tk()
    Panel(root, args.flag)
    root.mainloop()


if __name__ == "__main__":
    main()
