"""工具：用 IMAP 拉取自己邮箱里最新一封「AI 日报」邮件，存成 txt（作业2 的收信自证）。

用法：python tools/imap_check.py [out.txt]
凭据取环境变量 SMTP_USER / SMTP_PASS（.env 已加载）。
"""
import os
import sys
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE, ".env"))

USER = os.environ.get("SMTP_USER", "")
PASS = os.environ.get("SMTP_PASS", "")
HOST = os.environ.get("IMAP_HOST", "imap.qq.com")


def _dec(s):
    if not s:
        return ""
    out = []
    for part, enc in decode_header(s):
        if isinstance(part, bytes):
            out.append(part.decode(enc or "utf-8", "replace"))
        else:
            out.append(part)
    return "".join(out)


def latest_mail(subject_contains="AI 日报"):
    M = imaplib.IMAP4_SSL(HOST, 993)
    M.login(USER, PASS)
    M.select("INBOX")
    typ, data = M.search(None, 'ALL')
    ids = data[0].split()
    if not ids:
        M.logout()
        return None
    for mid in reversed(ids[-10:]):
        typ, msg_data = M.fetch(mid, "(RFC822)")
        if not msg_data or not msg_data[0]:
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        subj = _dec(msg.get("Subject", ""))
        date = msg.get("Date", "")
        if subject_contains in subj:
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode("utf-8", "replace")
            else:
                body = msg.get_payload(decode=True).decode("utf-8", "replace")
            M.logout()
            return {"subject": subj, "date": date, "from": _dec(msg.get("From", "")), "body": body}
    M.logout()
    return None


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "logs", "latest_mail.txt")
    info = latest_mail()
    if not info:
        print("[imap] 未找到「AI 日报」邮件")
        sys.exit(2)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"主题：{info['subject']}\n")
        f.write(f"发件人：{info['from']}\n")
        f.write(f"收件时间：{info['date']}\n")
        f.write("=" * 60 + "\n")
        f.write(info["body"])
    print(f"[imap] 已写入 {out}（主题：{info['subject']}）")
