"""② 盘家底：遍历本机指定目录，整理「数据 / 代码技能 / 文档」地图（markdown）。

产出三部分：分类清单 + 目录分布 + 体量统计——即「我的机器上有什么、都在哪、干什么用」。
"""
import os
from collections import Counter
from config import SCAN_ROOTS, IGNORE_DIRS

DATA_EXT = {".csv", ".xlsx", ".xls", ".json", ".jsonl", ".parquet", ".db", ".sqlite"}
CODE_EXT = {".py", ".ipynb", ".js", ".ts", ".r", ".sql", ".html", ".md"}
DOC_EXT = {".pdf", ".pptx", ".docx", ".txt"}


def scan():
    rows = []
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            print(f"[inv] 跳过不存在的目录：{root}")
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in DATA_EXT:
                    kind = "数据"
                elif ext in CODE_EXT:
                    kind = "代码/技能"
                elif ext in DOC_EXT:
                    kind = "文档"
                else:
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                try:
                    size = os.path.getsize(os.path.join(dirpath, fn))
                except OSError:
                    size = 0
                rows.append((kind, root.split(os.sep)[-1], rel, size))
    return rows


def to_markdown(rows):
    total = len(rows)
    kind_count = Counter(r[0] for r in rows)
    size_sum = sum(r[3] for r in rows)
    lines = [
        "# 本机家底地图",
        "",
        f"> 自动生成：共 {total} 个文件、{size_sum / 1024 / 1024:.1f} MB。"
        f" 数据 {kind_count.get('数据', 0)} / 代码技能 {kind_count.get('代码/技能', 0)} / 文档 {kind_count.get('文档', 0)}。",
        "",
    ]
    for kind in ("数据", "代码/技能", "文档"):
        items = [r for r in rows if r[0] == kind]
        lines.append(f"## {kind}（{len(items)}）")
        if not items:
            lines.append("_（该根目录无此类文件）_")
            lines.append("")
            continue
        for _, rootname, rel, size in sorted(items, key=lambda x: -x[3])[:200]:  # 按体量排序，截断避免过长
            lines.append(f"- `{rootname}/{rel}`（{size / 1024:.0f} KB）")
        if len(items) > 200:
            lines.append(f"- …（另有 {len(items)-200} 个未列）")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(to_markdown(scan()))
