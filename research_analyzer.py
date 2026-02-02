"""
研究分析和摘要生成模組
分析 PubMed 文獻，生成摘要，識別研究趨勢，提供研究想法
"""

import json
import os
from datetime import datetime
from collections import Counter, defaultdict
from typing import Optional
import re

from config import (
    TREND_KEYWORDS, DATA_DIR, SUMMARY_FILE, TRENDS_FILE,
    HIGH_IMPACT_JOURNALS
)


class ResearchAnalyzer:
    """研究分析器"""

    def __init__(self, articles_data: Optional[dict] = None):
        """
        初始化研究分析器

        Args:
            articles_data: 文章資料字典
        """
        self.articles_data = articles_data or {}

    def load_articles(self, filepath: str) -> None:
        """載入文章資料"""
        with open(filepath, "r", encoding="utf-8") as f:
            self.articles_data = json.load(f)

    def get_all_articles(self) -> list[dict]:
        """獲取所有文章的扁平列表"""
        all_articles = []
        for category, data in self.articles_data.items():
            for article in data.get("articles", []):
                article["category"] = category
                article["category_name"] = data.get("name", category)
                all_articles.append(article)
        return all_articles

    def analyze_trends(self) -> dict:
        """
        分析研究趨勢

        Returns:
            趨勢分析結果
        """
        all_articles = self.get_all_articles()
        if not all_articles:
            return {}

        trends = {
            "總文章數": len(all_articles),
            "高影響力期刊文章數": sum(1 for a in all_articles if a.get("is_high_impact")),
            "分析日期": datetime.now().isoformat(),
            "趨勢關鍵詞統計": {},
            "熱門主題": [],
            "期刊分布": {},
            "文章類型分布": {},
            "MeSH詞彙頻率": {},
            "按類別統計": {}
        }

        # 趨勢關鍵詞分析
        keyword_counts = defaultdict(lambda: defaultdict(int))
        for article in all_articles:
            text = f"{article.get('title', '')} {article.get('abstract', '')}".lower()
            for category, keywords in TREND_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        keyword_counts[category][keyword] += 1

        trends["趨勢關鍵詞統計"] = {
            cat: dict(sorted(kws.items(), key=lambda x: x[1], reverse=True))
            for cat, kws in keyword_counts.items()
        }

        # 熱門主題 (基於所有趨勢關鍵詞)
        all_keyword_counts = Counter()
        for kws in keyword_counts.values():
            all_keyword_counts.update(kws)
        trends["熱門主題"] = all_keyword_counts.most_common(20)

        # 期刊分布
        journal_counts = Counter(a.get("journal", "Unknown") for a in all_articles)
        trends["期刊分布"] = dict(journal_counts.most_common(15))

        # 文章類型分布
        pub_type_counts = Counter()
        for article in all_articles:
            for pt in article.get("pub_types", []):
                pub_type_counts[pt] += 1
        trends["文章類型分布"] = dict(pub_type_counts.most_common(10))

        # MeSH 詞彙頻率
        mesh_counts = Counter()
        for article in all_articles:
            mesh_counts.update(article.get("mesh_terms", []))
        trends["MeSH詞彙頻率"] = dict(mesh_counts.most_common(30))

        # 按類別統計
        for category, data in self.articles_data.items():
            articles = data.get("articles", [])
            trends["按類別統計"][data.get("name", category)] = {
                "文章數": len(articles),
                "高影響力期刊文章數": sum(1 for a in articles if a.get("is_high_impact")),
                "主要期刊": dict(Counter(a.get("journal", "") for a in articles).most_common(5))
            }

        return trends

    def extract_pico(self, article: dict) -> dict:
        """
        從文章中提取 PICO 格式資訊
        P (Population): 研究族群
        I (Intervention): 介入措施
        C (Comparison): 對照組
        O (Outcome): 結果指標

        Args:
            article: 文章資料

        Returns:
            PICO 格式字典
        """
        abstract = article.get("abstract", "")
        title = article.get("title", "")
        text = f"{title} {abstract}"

        pico = {
            "P_族群": "",
            "I_介入": "",
            "C_對照": "",
            "O_結果": ""
        }

        # Population 提取模式
        population_patterns = [
            r"(?:patients?|subjects?|participants?|children|adults?|individuals?)\s+(?:with|who|having)\s+([^.]+?)(?:\.|,|were|was)",
            r"(?:in|among)\s+(\d+[\d,]*\s*(?:patients?|subjects?|participants?|children|adults?)(?:[^.]{0,100}))",
            r"(\d+[\d,]*\s*(?:patients?|subjects?|participants?|children|adults?)[^.]{0,50}(?:with|having)[^.]{0,100})",
            r"(?:enrolled|included|recruited)\s+(\d+[^.]{0,150})",
        ]

        for pattern in population_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pico["P_族群"] = match.group(1).strip()[:200]
                break

        # Intervention 提取模式
        intervention_patterns = [
            r"(?:received|treated with|administered|given|assigned to)\s+([^.]+?)(?:\.|,|versus|vs|compared|or placebo)",
            r"(?:intervention|treatment)\s+(?:group|arm)?\s*(?:received|was|included)?\s*([^.]+?)(?:\.|,|versus|vs)",
            r"(?:effect of|efficacy of|impact of)\s+([^.]+?)\s+(?:on|in|for)",
        ]

        for pattern in intervention_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pico["I_介入"] = match.group(1).strip()[:200]
                break

        # Comparison 提取模式
        comparison_patterns = [
            r"(?:compared (?:to|with)|versus|vs\.?)\s+([^.]+?)(?:\.|,|in terms)",
            r"(?:control group|placebo group)\s*(?:received|was)?\s*([^.]*)",
            r"(?:placebo|standard care|usual care|conventional treatment)",
        ]

        for pattern in comparison_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1).strip() if match.lastindex else match.group(0).strip()
                pico["C_對照"] = result[:200]
                break

        # Outcome 提取模式
        outcome_patterns = [
            r"(?:primary (?:outcome|endpoint)|main outcome)\s*(?:was|were|included)?\s*([^.]+)",
            r"(?:measured|assessed|evaluated)\s+([^.]+?)(?:\.|,|using|by)",
            r"(?:significantly|showed)\s+([^.]+?)(?:\.|,)",
            r"(?:reduction|increase|improvement|decrease|change)\s+(?:in|of)\s+([^.]+?)(?:\.|,)",
        ]

        for pattern in outcome_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pico["O_結果"] = match.group(1).strip()[:200]
                break

        # 如果沒提取到，從 MeSH 詞彙補充
        mesh_terms = article.get("mesh_terms", [])
        if not pico["P_族群"] and mesh_terms:
            disease_terms = [m for m in mesh_terms if any(kw in m.lower() for kw in
                ["disease", "syndrome", "disorder", "injury", "failure", "nephro", "kidney", "renal"])]
            if disease_terms:
                pico["P_族群"] = f"患有 {', '.join(disease_terms[:2])} 的病人"

        return pico

    def generate_chinese_summary(self, article: dict) -> str:
        """
        生成中文摘要

        Args:
            article: 文章資料

        Returns:
            中文摘要字串
        """
        abstract = article.get("abstract", "")
        title = article.get("title", "")
        pub_types = article.get("pub_types", [])

        # 識別研究類型
        study_type = "本研究"
        if any("Randomized Controlled Trial" in pt for pt in pub_types):
            study_type = "本隨機對照試驗"
        elif any("Meta-Analysis" in pt for pt in pub_types):
            study_type = "本統合分析"
        elif any("Systematic Review" in pt for pt in pub_types):
            study_type = "本系統性回顧"
        elif "cohort" in abstract.lower():
            study_type = "本世代研究"
        elif "case-control" in abstract.lower():
            study_type = "本病例對照研究"

        # 提取各部分
        sections = {}
        section_patterns = [
            (r"BACKGROUND[:\s]*(.+?)(?=METHODS|OBJECTIVE|AIM|PURPOSE|$)", "背景"),
            (r"(?:OBJECTIVE|AIM|PURPOSE)[S]?[:\s]*(.+?)(?=METHODS|DESIGN|$)", "目的"),
            (r"METHODS[:\s]*(.+?)(?=RESULTS|FINDINGS|$)", "方法"),
            (r"(?:RESULTS|FINDINGS)[:\s]*(.+?)(?=CONCLUSIONS?|DISCUSSION|INTERPRETATION|$)", "結果"),
            (r"(?:CONCLUSIONS?|INTERPRETATION)[:\s]*(.+?)$", "結論"),
        ]

        for pattern, section_name in section_patterns:
            match = re.search(pattern, abstract, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section_name] = match.group(1).strip()

        # 建構中文摘要
        summary_parts = []

        # 研究目的
        if "目的" in sections:
            summary_parts.append(f"【研究目的】{study_type}旨在探討{self._simplify_text(sections['目的'])}")
        elif "背景" in sections:
            summary_parts.append(f"【研究背景】{self._simplify_text(sections['背景'])}")

        # 研究方法
        if "方法" in sections:
            summary_parts.append(f"【研究方法】{self._simplify_text(sections['方法'])}")

        # 研究結果
        if "結果" in sections:
            summary_parts.append(f"【主要結果】{self._simplify_text(sections['結果'])}")

        # 結論
        if "結論" in sections:
            summary_parts.append(f"【結論】{self._simplify_text(sections['結論'])}")

        if summary_parts:
            return "\n\n".join(summary_parts)
        else:
            # 如果沒有結構化摘要，直接返回簡化的原始摘要
            return f"【摘要】{self._simplify_text(abstract[:800])}"

    def _simplify_text(self, text: str, max_length: int = 300) -> str:
        """簡化文字，移除多餘空白並截斷"""
        # 移除多餘空白和換行
        text = re.sub(r'\s+', ' ', text).strip()
        # 截斷但保持句子完整
        if len(text) > max_length:
            # 在最大長度附近找句號
            cut_point = text.rfind('.', 0, max_length)
            if cut_point > max_length * 0.5:
                text = text[:cut_point + 1]
            else:
                text = text[:max_length] + "..."
        return text

    def generate_article_summary(self, article: dict) -> dict:
        """
        為單篇文章生成摘要（含 PICO 格式和中文摘要）

        Args:
            article: 文章資料

        Returns:
            文章摘要
        """
        # 提取關鍵資訊
        abstract = article.get("abstract", "")

        # 嘗試從結構化摘要中提取
        sections = {}
        section_patterns = [
            (r"BACKGROUND[:\s]*(.+?)(?=METHODS|OBJECTIVE|$)", "背景"),
            (r"OBJECTIVE[S]?[:\s]*(.+?)(?=METHODS|RESULTS|$)", "目的"),
            (r"METHODS[:\s]*(.+?)(?=RESULTS|$)", "方法"),
            (r"RESULTS[:\s]*(.+?)(?=CONCLUSIONS?|DISCUSSION|$)", "結果"),
            (r"CONCLUSIONS?[:\s]*(.+?)$", "結論"),
        ]

        for pattern, section_name in section_patterns:
            match = re.search(pattern, abstract, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section_name] = match.group(1).strip()[:500]

        # 識別研究類型
        pub_types = article.get("pub_types", [])
        study_type = "研究"
        if any("Randomized Controlled Trial" in pt for pt in pub_types):
            study_type = "隨機對照試驗"
        elif any("Meta-Analysis" in pt for pt in pub_types):
            study_type = "統合分析"
        elif any("Systematic Review" in pt for pt in pub_types):
            study_type = "系統性回顧"
        elif any("Cohort" in abstract.lower() for _ in [1]):
            study_type = "世代研究"
        elif any("Case-Control" in abstract.lower() for _ in [1]):
            study_type = "病例對照研究"

        # 識別相關趨勢關鍵詞
        text = f"{article.get('title', '')} {abstract}".lower()
        related_trends = []
        for category, keywords in TREND_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    related_trends.append(f"{category}: {keyword}")

        # 提取 PICO 格式
        pico = self.extract_pico(article)

        # 生成中文摘要
        chinese_summary = self.generate_chinese_summary(article)

        return {
            "pmid": article.get("pmid"),
            "標題": article.get("title"),
            "期刊": article.get("journal"),
            "發表日期": article.get("pub_date"),
            "研究類型": study_type,
            "PICO": pico,
            "中文摘要": chinese_summary,
            "結構化摘要": sections if sections else {"完整摘要": abstract[:1000]},
            "相關趨勢": related_trends[:5],
            "關鍵詞": article.get("keywords", [])[:10],
            "MeSH詞彙": article.get("mesh_terms", [])[:10],
            "是否高影響力期刊": article.get("is_high_impact", False),
            "PubMed連結": article.get("pubmed_url"),
            "DOI": article.get("doi")
        }

    def generate_research_ideas(self) -> list[dict]:
        """
        基於當前研究趨勢生成研究想法

        Returns:
            研究想法列表
        """
        trends = self.analyze_trends()
        all_articles = self.get_all_articles()

        ideas = []

        # 1. 基於熱門主題的研究想法
        hot_topics = trends.get("熱門主題", [])[:10]
        for topic, count in hot_topics:
            ideas.append({
                "類型": "熱門主題延伸",
                "關鍵詞": topic,
                "頻率": count,
                "想法": f"目前 '{topic}' 是研究熱點 ({count} 篇相關文章)，可考慮：\n"
                       f"1. 在本地族群中驗證相關發現\n"
                       f"2. 結合其他熱門主題進行交叉研究\n"
                       f"3. 針對特定亞群進行深入分析",
                "建議研究類型": "觀察性研究 / 回顧性分析"
            })

        # 2. 基於研究缺口的想法
        keyword_stats = trends.get("趨勢關鍵詞統計", {})

        # 找出相對較少研究的新興主題
        all_keywords = {}
        for cat, kws in keyword_stats.items():
            for kw, count in kws.items():
                all_keywords[kw] = {"count": count, "category": cat}

        if all_keywords:
            # 找出提及但研究較少的主題
            low_count_keywords = [
                (kw, data) for kw, data in all_keywords.items()
                if 1 <= data["count"] <= 3
            ]

            for kw, data in low_count_keywords[:5]:
                ideas.append({
                    "類型": "研究缺口",
                    "關鍵詞": kw,
                    "頻率": data["count"],
                    "想法": f"'{kw}' ({data['category']}) 目前研究較少 ({data['count']} 篇)，\n"
                           f"可能是新興或未被充分探索的領域，可考慮：\n"
                           f"1. 文獻回顧以了解現有證據\n"
                           f"2. 前瞻性觀察研究\n"
                           f"3. 與既有研究主題結合",
                    "建議研究類型": "系統性回顧 / 前瞻性研究"
                })

        # 3. 跨領域研究想法
        categories_with_articles = [
            (cat, data) for cat, data in self.articles_data.items()
            if data.get("articles")
        ]

        if len(categories_with_articles) >= 2:
            ideas.append({
                "類型": "跨領域研究",
                "關鍵詞": "兒童腎臟學 + 成人腎臟學",
                "想法": "考慮進行兒童至成人的長期追蹤研究：\n"
                       "1. 兒童期腎臟疾病對成年後的影響\n"
                       "2. 早期介入對長期預後的效果\n"
                       "3. 生命歷程觀點的腎臟病研究",
                "建議研究類型": "長期追蹤世代研究"
            })

        # 4. 方法學創新想法
        method_ideas = [
            {
                "類型": "方法學創新",
                "關鍵詞": "AI/機器學習",
                "想法": "應用人工智慧於腎臟病研究：\n"
                       "1. 建立腎功能預測模型\n"
                       "2. 影像自動判讀系統\n"
                       "3. 治療反應預測",
                "建議研究類型": "回顧性資料分析 + 模型開發"
            },
            {
                "類型": "方法學創新",
                "關鍵詞": "真實世界數據",
                "想法": "利用真實世界數據進行研究：\n"
                       "1. 健保資料庫分析\n"
                       "2. 電子病歷數據挖掘\n"
                       "3. 多中心登錄資料分析",
                "建議研究類型": "真實世界研究 (RWE)"
            }
        ]
        ideas.extend(method_ideas)

        # 5. 根據高影響力文章的啟發
        high_impact_articles = [a for a in all_articles if a.get("is_high_impact")]
        if high_impact_articles:
            ideas.append({
                "類型": "高影響力研究延伸",
                "關鍵詞": "重要發現複製與延伸",
                "想法": f"本週有 {len(high_impact_articles)} 篇高影響力期刊文章，可考慮：\n"
                       "1. 在本地族群中驗證這些發現\n"
                       "2. 探索可能的機轉\n"
                       "3. 研究是否有族群差異",
                "相關文章": [a.get("title", "")[:50] for a in high_impact_articles[:3]],
                "建議研究類型": "驗證性研究 / 機轉研究"
            })

        return ideas

    def generate_weekly_summary(self) -> dict:
        """
        生成每週研究摘要

        Returns:
            完整的每週摘要
        """
        trends = self.analyze_trends()
        all_articles = self.get_all_articles()
        research_ideas = self.generate_research_ideas()

        # 選擇重點文章 (高影響力優先)
        featured_articles = sorted(
            all_articles,
            key=lambda x: (x.get("is_high_impact", False), x.get("pub_date", "")),
            reverse=True
        )[:10]

        summary = {
            "報告日期": datetime.now().isoformat(),
            "報告週期": f"過去 {self.articles_data.get(list(self.articles_data.keys())[0], {}).get('days_back', 7)} 天" if self.articles_data else "N/A",

            "執行摘要": {
                "總文章數": trends.get("總文章數", 0),
                "高影響力期刊文章數": trends.get("高影響力期刊文章數", 0),
                "主要發現": self._generate_key_findings(all_articles, trends),
            },

            "分類統計": trends.get("按類別統計", {}),

            "研究趨勢": {
                "熱門主題": trends.get("熱門主題", [])[:10],
                "趨勢關鍵詞": trends.get("趨勢關鍵詞統計", {}),
                "期刊分布": trends.get("期刊分布", {}),
                "文章類型": trends.get("文章類型分布", {}),
            },

            "重點文章": [
                self.generate_article_summary(article)
                for article in featured_articles
            ],

            "研究想法": research_ideas,

            "MeSH詞彙分析": trends.get("MeSH詞彙頻率", {}),
        }

        return summary

    def _generate_key_findings(self, articles: list[dict], trends: dict) -> list[str]:
        """生成主要發現摘要"""
        findings = []

        # 熱門主題
        hot_topics = trends.get("熱門主題", [])[:3]
        if hot_topics:
            topic_str = ", ".join([f"{t[0]} ({t[1]}篇)" for t in hot_topics])
            findings.append(f"本週熱門研究主題: {topic_str}")

        # 高影響力期刊
        high_impact = [a for a in articles if a.get("is_high_impact")]
        if high_impact:
            journals = list(set(a.get("journal", "") for a in high_impact))[:3]
            findings.append(f"高影響力期刊發表 {len(high_impact)} 篇，包括: {', '.join(journals)}")

        # 研究類型分布
        pub_types = trends.get("文章類型分布", {})
        rct_count = pub_types.get("Randomized Controlled Trial", 0)
        meta_count = pub_types.get("Meta-Analysis", 0)
        if rct_count or meta_count:
            findings.append(f"高品質證據: {rct_count} 篇 RCT, {meta_count} 篇統合分析")

        return findings

    def save_summary(self, summary: dict, filepath: Optional[str] = None) -> None:
        """儲存摘要到檔案"""
        if filepath is None:
            os.makedirs(DATA_DIR, exist_ok=True)
            filepath = os.path.join(DATA_DIR, SUMMARY_FILE)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"摘要已儲存至: {filepath}")

    def save_trends(self, trends: dict, filepath: Optional[str] = None) -> None:
        """儲存趨勢分析到檔案"""
        if filepath is None:
            os.makedirs(DATA_DIR, exist_ok=True)
            filepath = os.path.join(DATA_DIR, TRENDS_FILE)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trends, f, ensure_ascii=False, indent=2)

        print(f"趨勢分析已儲存至: {filepath}")


def main():
    """測試用主程式"""
    from pubmed_fetcher import PubMedFetcher

    # 抓取文章
    fetcher = PubMedFetcher()
    articles = fetcher.fetch_nephrology_articles(days_back=7)
    fetcher.save_articles(articles)

    # 分析
    analyzer = ResearchAnalyzer(articles)

    # 生成趨勢
    trends = analyzer.analyze_trends()
    analyzer.save_trends(trends)

    # 生成每週摘要
    summary = analyzer.generate_weekly_summary()
    analyzer.save_summary(summary)

    print("\n=== 執行摘要 ===")
    print(json.dumps(summary["執行摘要"], ensure_ascii=False, indent=2))

    print("\n=== 研究想法 ===")
    for idea in summary["研究想法"][:3]:
        print(f"\n{idea['類型']}: {idea['關鍵詞']}")
        print(idea["想法"])


if __name__ == "__main__":
    main()
