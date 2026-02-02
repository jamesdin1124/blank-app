#!/usr/bin/env python3
"""
Email 報告生成模組
生成 HTML 格式的每週腎臟學研究摘要報告
"""

import json
import os
from datetime import datetime
from typing import Optional

from config import DATA_DIR, SUMMARY_FILE


def generate_html_report(summary: Optional[dict] = None) -> str:
    """
    生成 HTML 格式的 Email 報告

    Args:
        summary: 摘要資料，若為 None 則從檔案載入

    Returns:
        HTML 格式的報告字串
    """
    if summary is None:
        summary_path = os.path.join(DATA_DIR, SUMMARY_FILE)
        if not os.path.exists(summary_path):
            return "<p>無可用的摘要資料</p>"
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    exec_summary = summary.get("執行摘要", {})
    category_stats = summary.get("分類統計", {})
    research_trends = summary.get("研究趨勢", {})
    featured_articles = summary.get("重點文章", [])[:5]
    research_ideas = summary.get("研究想法", [])[:3]

    # 報告日期
    report_date = summary.get("報告日期", "")
    try:
        dt = datetime.fromisoformat(report_date)
        formatted_date = dt.strftime("%Y年%m月%d日")
    except (ValueError, TypeError):
        formatted_date = datetime.now().strftime("%Y年%m月%d日")

    html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>腎臟學研究週報 - {formatted_date}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #1E3A5F;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1E3A5F;
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            color: #666;
            margin: 10px 0 0 0;
        }}
        .metrics {{
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin: 20px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .metric {{
            text-align: center;
            padding: 10px 20px;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            color: #1E3A5F;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #1E3A5F;
            border-left: 4px solid #1E3A5F;
            padding-left: 15px;
            margin-bottom: 15px;
        }}
        .finding {{
            background-color: #e8f4ea;
            border-left: 4px solid #28a745;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }}
        .article {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            background-color: #fafafa;
        }}
        .article-title {{
            font-weight: bold;
            color: #1E3A5F;
            margin-bottom: 8px;
        }}
        .article-meta {{
            font-size: 13px;
            color: #666;
        }}
        .high-impact {{
            display: inline-block;
            background-color: #FFD700;
            color: #333;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .trend-tag {{
            display: inline-block;
            background-color: #e3f2fd;
            color: #1565c0;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 12px;
            margin: 3px;
        }}
        .idea {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 5px 5px 0;
        }}
        .idea-type {{
            font-weight: bold;
            color: #e65100;
            margin-bottom: 5px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 12px;
        }}
        a {{
            color: #1565c0;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        @media (max-width: 600px) {{
            .metrics {{
                flex-direction: column;
            }}
            .metric {{
                margin: 10px 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>腎臟學研究週報</h1>
            <p>{formatted_date} | 自動追蹤最新高品質腎臟學臨床研究</p>
        </div>

        <!-- 關鍵指標 -->
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{exec_summary.get('總文章數', 0)}</div>
                <div class="metric-label">總文章數</div>
            </div>
            <div class="metric">
                <div class="metric-value">{exec_summary.get('高影響力期刊文章數', 0)}</div>
                <div class="metric-label">高影響力期刊</div>
            </div>
            <div class="metric">
                <div class="metric-value">{category_stats.get('兒童腎臟學', {}).get('文章數', 0)}</div>
                <div class="metric-label">兒童腎臟學</div>
            </div>
            <div class="metric">
                <div class="metric-value">{category_stats.get('成人腎臟學', {}).get('文章數', 0)}</div>
                <div class="metric-label">成人腎臟學</div>
            </div>
        </div>

        <!-- 主要發現 -->
        <div class="section">
            <h2>本週重點發現</h2>
"""

    # 主要發現
    findings = exec_summary.get("主要發現", [])
    if findings:
        for finding in findings:
            html += f'            <div class="finding">{finding}</div>\n'
    else:
        html += '            <div class="finding">本週暫無特別發現</div>\n'

    html += """
        </div>

        <!-- 熱門研究主題 -->
        <div class="section">
            <h2>熱門研究主題</h2>
            <div>
"""

    # 熱門主題
    hot_topics = research_trends.get("熱門主題", [])[:10]
    if hot_topics:
        for topic, count in hot_topics:
            html += f'                <span class="trend-tag">{topic} ({count})</span>\n'
    else:
        html += '                <p>本週暫無熱門主題</p>\n'

    html += """
            </div>
        </div>

        <!-- 重點文章 -->
        <div class="section">
            <h2>重點文章</h2>
"""

    # 重點文章
    if featured_articles:
        for article in featured_articles:
            title = article.get("標題", "無標題")
            journal = article.get("期刊", "N/A")
            study_type = article.get("研究類型", "研究")
            pub_date = article.get("發表日期", "")
            is_high_impact = article.get("是否高影響力期刊", False)
            pubmed_url = article.get("PubMed連結", "")

            high_impact_badge = '<span class="high-impact">高影響力期刊</span>' if is_high_impact else ''

            html += f"""
            <div class="article">
                <div class="article-title">
                    {title}{high_impact_badge}
                </div>
                <div class="article-meta">
                    {journal} | {study_type} | {pub_date}
                    {f'<br><a href="{pubmed_url}" target="_blank">在 PubMed 查看</a>' if pubmed_url else ''}
                </div>
            </div>
"""
    else:
        html += '            <p>本週暫無重點文章</p>\n'

    html += """
        </div>

        <!-- 研究想法 -->
        <div class="section">
            <h2>研究想法建議</h2>
"""

    # 研究想法
    if research_ideas:
        for idea in research_ideas:
            idea_type = idea.get("類型", "")
            keyword = idea.get("關鍵詞", "")
            content = idea.get("想法", "").replace("\n", "<br>")
            suggested_type = idea.get("建議研究類型", "")

            html += f"""
            <div class="idea">
                <div class="idea-type">[{idea_type}] {keyword}</div>
                <p>{content}</p>
                <p><strong>建議研究類型:</strong> {suggested_type}</p>
            </div>
"""
    else:
        html += '            <p>分析資料後將生成研究想法建議</p>\n'

    html += f"""
        </div>

        <!-- 頁尾 -->
        <div class="footer">
            <p>此報告由 PubMed 腎臟學研究週報系統自動生成</p>
            <p>報告時間: {formatted_date}</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def save_html_report(html: str, filepath: Optional[str] = None) -> str:
    """
    儲存 HTML 報告到檔案

    Args:
        html: HTML 內容
        filepath: 檔案路徑，若為 None 則使用預設路徑

    Returns:
        儲存的檔案路徑
    """
    if filepath is None:
        os.makedirs(DATA_DIR, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        filepath = os.path.join(DATA_DIR, f"report_{date_str}.html")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML 報告已儲存至: {filepath}")
    return filepath


def main():
    """測試用主程式"""
    html = generate_html_report()
    filepath = save_html_report(html)
    print(f"報告已生成: {filepath}")


if __name__ == "__main__":
    main()
