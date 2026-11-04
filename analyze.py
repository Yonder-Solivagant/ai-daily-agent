"""③ 分析：把「新 AI 资讯」与「本机家底」交给 LLM，生成一份带洞察的日报。

LLM 不可用（没配 key / 调用失败）时自动退化为纯汇编，保证机器永远能出结果。
"""
from net import post as http_post
from config import LLM_BASE, LLM_KEY, LLM_MODEL

SYSTEM = ("你是研究助理。输入是：A) 近期抓到的 AI 资讯条目；B) 用户本机已有数据与技能地图。"
          "产出一份简洁中文日报：1) 本期 AI 要点（3-5 条，附来源链接）；"
          "2) 哪些新动向可与本机已有资料/技能结合（点到具体文件或技能）；3) 一句今日建议。"
          "不要编造链接，链接只用输入里出现的。")


def build_report(new_items, inventory_md):
    news = "\n".join(
        f"- [{it['source']}] {it['title']}  {it['link']}" for it in new_items
    ) or "（本期无新资讯）"
    user = f"【A 新资讯】\n{news}\n\n【B 本机家底（节选）】\n{inventory_md[:4000]}"
    if not LLM_KEY:
        print("[llm] 未配置 LLM_KEY，退化为纯汇编")
        return f"# AI 日报（未接 LLM，纯汇编）\n\n## 新资讯\n{news}\n\n## 本机家底\n{inventory_md[:3000]}"
    prompt = f"【A 新资讯】\n{news}\n\n【B 本机家底（节选）】\n{inventory_md[:4000]}"
    try:
        resp = http_post(
            f"{LLM_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {LLM_KEY}", "Content-Type": "application/json"},
            json={"model": LLM_MODEL, "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ], "temperature": 0.3},
            timeout=110,
        )
        print(f"[llm] {LLM_MODEL} 生成日报成功")
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[llm] 调用失败（{e}），退化为纯汇编")
        return f"# AI 日报（LLM 调用失败，纯汇编）\n\n## 新资讯\n{news}\n\n## 本机家底\n{inventory_md[:3000]}"


if __name__ == "__main__":
    from rss_watch import pull_new
    from inventory import scan, to_markdown
    print(build_report(pull_new(), to_markdown(scan())))
