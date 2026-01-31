#!/usr/bin/env python3
"""
每週 PubMed 文獻抓取腳本
可透過 GitHub Actions 或手動執行
"""

import argparse
import json
import os
import sys
from datetime import datetime

from pubmed_fetcher import PubMedFetcher
from research_analyzer import ResearchAnalyzer
from config import DATA_DIR


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="抓取 PubMed 腎臟學最新文獻"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="搜尋過去幾天的文獻 (預設: 7)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="每類別最大文章數 (預設: 50)"
    )
    parser.add_argument(
        "--high-impact-only",
        action="store_true",
        help="僅抓取高影響力期刊文章"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DATA_DIR,
        help=f"輸出目錄 (預設: {DATA_DIR})"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("腎臟學研究週報 - PubMed 文獻抓取")
    print("=" * 60)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"搜尋範圍: 過去 {args.days_back} 天")
    print(f"每類別最大文章數: {args.max_results}")
    print(f"僅高影響力期刊: {args.high_impact_only}")
    print("=" * 60)

    # 確保輸出目錄存在
    os.makedirs(args.output_dir, exist_ok=True)

    # 初始化抓取器
    fetcher = PubMedFetcher()

    # 抓取文章
    print("\n正在從 PubMed 抓取文獻...")
    try:
        articles = fetcher.fetch_nephrology_articles(
            category="all",
            max_results=args.max_results,
            days_back=args.days_back,
            high_impact_only=args.high_impact_only
        )
    except Exception as e:
        print(f"抓取文獻時發生錯誤: {e}")
        sys.exit(1)

    # 儲存文章
    articles_path = os.path.join(args.output_dir, "articles.json")
    fetcher.save_articles(articles, articles_path)

    # 分析文章
    print("\n正在分析文獻...")
    analyzer = ResearchAnalyzer(articles)

    # 生成趨勢分析
    trends = analyzer.analyze_trends()
    trends_path = os.path.join(args.output_dir, "trends.json")
    analyzer.save_trends(trends, trends_path)

    # 生成每週摘要
    summary = analyzer.generate_weekly_summary()
    summary_path = os.path.join(args.output_dir, "weekly_summary.json")
    analyzer.save_summary(summary, summary_path)

    # 顯示摘要
    print("\n" + "=" * 60)
    print("執行摘要")
    print("=" * 60)

    exec_summary = summary.get("執行摘要", {})
    print(f"總文章數: {exec_summary.get('總文章數', 0)}")
    print(f"高影響力期刊文章數: {exec_summary.get('高影響力期刊文章數', 0)}")

    print("\n主要發現:")
    for finding in exec_summary.get("主要發現", []):
        print(f"  - {finding}")

    # 按類別顯示統計
    print("\n分類統計:")
    for cat_name, cat_stats in summary.get("分類統計", {}).items():
        print(f"  {cat_name}: {cat_stats.get('文章數', 0)} 篇")

    # 顯示熱門主題
    print("\n熱門研究主題:")
    hot_topics = summary.get("研究趨勢", {}).get("熱門主題", [])[:5]
    for topic, count in hot_topics:
        print(f"  - {topic}: {count} 篇")

    # 顯示研究想法
    print("\n研究想法建議:")
    ideas = summary.get("研究想法", [])[:3]
    for idea in ideas:
        print(f"  [{idea.get('類型', '')}] {idea.get('關鍵詞', '')}")

    print("\n" + "=" * 60)
    print("抓取完成！")
    print(f"資料已儲存至: {args.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
