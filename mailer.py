"""③ 发送：把日报发到自己的邮箱（SMTP）。密钥走环境变量。

支持 465(SSL) 与 587(STARTTLS) 两种端口；发送失败会抛出异常由上层记录。
"""
import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.header import Header
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MAIL_TO


def send(subject, body):
    if not (SMTP_HOST and SMTP_USER and MAIL_TO):
        print("[mail] 未配置 SMTP，跳过发送。内容已打印：")
        print("==== 日报 ====")
        print(body[:2000])
        return False
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, [MAIL_TO], msg.as_string())
    print(f"[mail] 已发送至 {MAIL_TO}（{SMTP_HOST}:{SMTP_PORT} SSL）")
    return True


def send_robust(subject, body):
    """SSL 失败时退回 STARTTLS(587)，都失败则抛出异常。"""
    try:
        return send(subject, body)
    except (smtplib.SMTPException, socket.error, OSError) as e:
        alt = 587 if SMTP_PORT == 465 else 465
        print(f"[mail] {SMTP_HOST}:{SMTP_PORT} 失败（{e}），改试 {alt}")
        try:
            if alt == 465:
                return send_via(subject, body, alt, ssl=True)
            return send_via(subject, body, alt, ssl=False)
        except Exception as e2:
            print(f"[mail] 备用端口也失败：{e2}")
            raise


def send_via(subject, body, port, ssl=True):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    if ssl:
        with smtplib.SMTP_SSL(SMTP_HOST, port, timeout=30) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, [MAIL_TO], msg.as_string())
    else:
        with smtplib.SMTP(SMTP_HOST, port, timeout=30) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, [MAIL_TO], msg.as_string())
    print(f"[mail] 已发送至 {MAIL_TO}（{SMTP_HOST}:{port} {'SSL' if ssl else 'STARTTLS'}）")
    return True


if __name__ == "__main__":
    send_robust("测试邮件", "如果你看到这封，SMTP 配置成功。")
