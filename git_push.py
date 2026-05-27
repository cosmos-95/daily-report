import os
import sys
import shutil
import subprocess
import re
from datetime import datetime

REPO_DIR = r"C:\Users\28425\daily-report"
INDEX_FILE = os.path.join(REPO_DIR, "index.html")

# 中文星期映射
WEEKDAY_MAP = {
    0: "周一", 1: "周二", 2: "周三", 3: "周四",
    4: "周五", 5: "周六", 6: "周日"
}


def extract_from_html(html_path):
    """从报告HTML中提取摘要和高/中/低影响力事件数量"""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 从 <meta name="description"> 提取摘要
    summary = ""
    m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', content)
    if m:
        summary = m.group(1)

    # 从 <meta name="report-stats"> 提取统计数据
    high = mid = low = 0
    m = re.search(r'<meta\s+name="report-stats"\s+content="high:(\d+),mid:(\d+),low:(\d+)"', content)
    if m:
        high, mid, low = int(m.group(1)), int(m.group(2)), int(m.group(3))

    return summary, high, mid, low


def update_index(date_display, weekday, filename, summary, high, mid, low, is_ai):
    """更新index.html中的reports数组，在开头插入新条目"""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    tags = '["ai"]' if is_ai else '[]'

    new_entry = f'''  {{
    date: "{date_display}",
    weekday: "{weekday}",
    filename: "{filename}",
    summary: "{summary}",
    highCount: {high},
    midCount: {mid},
    lowCount: {low},
    tags: {tags}
  }}'''

    old = "const reports = ["
    new = f"const reports = [\n{new_entry}"
    content = content.replace(old, new, 1)

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  索引页已更新，新增条目: {date_display}")


def git_push_report(html_file_path, date_str):
    """推送报告到GitHub Pages并更新索引页"""
    try:
        filename = f"daily_report_{date_str}.html"
        target = os.path.join(REPO_DIR, filename)

        # 1. 复制报告到仓库
        shutil.copy2(html_file_path, target)
        print(f"  报告已复制: {target}")

        # 2. 提取报告元数据
        summary, high, mid, low = extract_from_html(target)
        if not summary:
            summary = "今日全球要闻报告"

        # 3. 解析日期信息
        dt = datetime.strptime(date_str, "%Y%m%d")
        date_display = f"{dt.year}年{dt.month}月{dt.day}日"
        weekday = WEEKDAY_MAP[dt.weekday()]
        is_ai = "ai" in summary.lower() or "AI" in summary or "大模型" in summary

        print(f"  日期: {date_display} {weekday}")
        print(f"  影响力: 高{high} 中{mid} 低{low}")

        # 4. 更新索引页
        update_index(date_display, weekday, filename, summary, high, mid, low, is_ai)

        # 5. Git操作
        subprocess.run(
            ["git", "add", filename, "index.html"],
            cwd=REPO_DIR, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"feat: 新增报告 {date_str} 并更新索引页"],
            cwd=REPO_DIR, check=True
        )
        subprocess.run(
            ["git", "push"],
            cwd=REPO_DIR, check=True
        )

        url = f"https://cosmos-95.github.io/daily-report/{filename}"
        index_url = "https://cosmos-95.github.io/daily-report/index.html"

        return {
            "success": True,
            "url": url,
            "index_url": index_url,
            "file": filename,
            "summary": summary[:60] + "..." if len(summary) > 60 else summary
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python git_push.py <html文件路径> <日期YYYYMMDD>")
        sys.exit(1)

    result = git_push_report(sys.argv[1], sys.argv[2])

    if result["success"]:
        print(f"\n  报告链接: {result['url']}")
        print(f"  索引页:   {result['index_url']}")
        print(f"  摘要:     {result['summary']}")
    else:
        print(f"\n  错误: {result['error']}")
        sys.exit(1)