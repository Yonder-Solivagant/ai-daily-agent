"""① 外部输入：拉取 AI RSS，只返回相比上次运行的新条目，并落盘到 store/。

网络策略：直连优先，直连失败自动改走 PROXY 代理（部分 RSS 站点直连不通）。
"""
import os
import json
import hashlib
import feedparser
from datetime import datetime
from config import FEEDS, STATE_FILE, STORE_DIR, MAX_ITEMS_PER_FEED
from net import get as http_get


def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, encoding="utf-8"))
        except Exception:
            pass
    return {"seen": []}


def _save_state(state):
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _fetch(url):
    """抓取 RSS（net 层内部做直连→代理降级），返回 feedparser 的解析结果。"""
    try:
        resp = http_get(url, timeout=30)
    except Exception as e:
        print(f"[rss] 抓取失败：{e}")
        return feedparser.parse("")
    parsed = feedparser.parse(resp.content)
    print(f"[rss] 抓到 {len(parsed.entries)} 条")
    return parsed


def pull_new():
    state = _load_state()
    seen = set(state.get("seen", []))
    os.makedirs(STORE_DIR, exist_ok=True)
    new_items = []
    for feed in FEEDS:
        print(f"[rss] 拉取 {feed['name']} <- {feed['url']}")
        parsed = _fetch(feed["url"])
        taken = 0
        for e in parsed.entries:
            if taken >= MAX_ITEMS_PER_FEED:
                break
            # 用 link 或 guid 做去重键
            key = e.get("id") or e.get("link") or e.get("title")
            if not key or key in seen:
                continue
            content = ""
            if "content" in e and e.content:
                content = e.content[0].value
            else:
                content = e.get("description", "")
            item = {
                "source": feed["name"],
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "published": e.get("published", ""),
                "summary": e.get("summary", ""),
                "content": content,
            }
            # 落盘（去 HTML 标签存纯文本备份）
            h = hashlib.md5(key.encode("utf-8")).hexdigest()[:12]
            txt = _strip_tags(content) or item["summary"]
            path = os.path.join(STORE_DIR, f"{feed['name']}_{h}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {item['title']}\n\n来源：{feed['name']}  \n链接：{item['link']}  \n时间：{item['published']}\n\n{txt}\n")
            item["file"] = path
            new_items.append(item)
            seen.add(key)
            taken += 1
    state["seen"] = list(seen)
    _save_state(state)
    print(f"[rss] 本次新增 {len(new_items)} 条")
    return new_items


def _strip_tags(html):
    import re
    txt = re.sub(r"<[^>]+>", "\n", html or "")
    txt = re.sub(r"\n{2,}", "\n\n", txt)
    return txt.strip()


if __name__ == "__main__":
    for it in pull_new():
        print("-", it["source"], it["title"])
