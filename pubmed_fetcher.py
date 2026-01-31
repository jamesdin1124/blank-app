"""
PubMed API 整合模組
使用 NCBI E-utilities 來搜尋和獲取腎臟學文獻
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional
import time
import json
import os
import re

from config import (
    PUBMED_SEARCH_URL, PUBMED_FETCH_URL,
    SEARCH_QUERIES, HIGH_IMPACT_JOURNALS,
    DEFAULT_MAX_RESULTS, DEFAULT_DAYS_BACK,
    DATA_DIR, ARTICLES_FILE
)


class PubMedFetcher:
    """PubMed 文獻抓取器"""

    def __init__(self, email: str = "researcher@example.com", api_key: Optional[str] = None):
        """
        初始化 PubMed 抓取器

        Args:
            email: NCBI 要求提供的 email (用於追蹤使用)
            api_key: NCBI API key (可選，有 key 可以增加請求頻率)
        """
        self.email = email
        self.api_key = api_key or os.environ.get("NCBI_API_KEY")
        self.session = requests.Session()

    def _make_request(self, url: str, params: dict) -> requests.Response:
        """發送 API 請求，包含重試邏輯"""
        params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        for attempt in range(3):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt < 2:
                    time.sleep(1 * (attempt + 1))
                else:
                    raise e
        return response

    def search_articles(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        days_back: int = DEFAULT_DAYS_BACK,
        sort: str = "relevance"
    ) -> list[str]:
        """
        搜尋 PubMed 文章

        Args:
            query: 搜尋查詢字串
            max_results: 最大結果數
            days_back: 搜尋過去幾天的文獻
            sort: 排序方式 (relevance, pub_date)

        Returns:
            PubMed ID 列表
        """
        # 計算日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_range = f"{start_date.strftime('%Y/%m/%d')}:{end_date.strftime('%Y/%m/%d')}[dp]"

        # 組合查詢
        full_query = f"({query}) AND {date_range}"

        params = {
            "db": "pubmed",
            "term": full_query,
            "retmax": max_results,
            "sort": sort,
            "retmode": "json"
        }

        response = self._make_request(PUBMED_SEARCH_URL, params)
        data = response.json()

        pmids = data.get("esearchresult", {}).get("idlist", [])
        return pmids

    def fetch_article_details(self, pmids: list[str]) -> list[dict]:
        """
        獲取文章詳細資訊

        Args:
            pmids: PubMed ID 列表

        Returns:
            文章詳細資訊列表
        """
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }

        response = self._make_request(PUBMED_FETCH_URL, params)

        # 解析 XML
        articles = self._parse_xml_response(response.text)
        return articles

    def _parse_xml_response(self, xml_text: str) -> list[dict]:
        """解析 PubMed XML 回應"""
        articles = []

        try:
            root = ET.fromstring(xml_text)

            for article_elem in root.findall(".//PubmedArticle"):
                article = self._parse_article(article_elem)
                if article:
                    articles.append(article)

        except ET.ParseError as e:
            print(f"XML 解析錯誤: {e}")

        return articles

    def _parse_article(self, article_elem: ET.Element) -> Optional[dict]:
        """解析單篇文章"""
        try:
            medline = article_elem.find(".//MedlineCitation")
            if medline is None:
                return None

            pmid = medline.findtext(".//PMID", "")
            article = medline.find(".//Article")
            if article is None:
                return None

            # 標題
            title = article.findtext(".//ArticleTitle", "")

            # 摘要
            abstract_parts = []
            abstract_elem = article.find(".//Abstract")
            if abstract_elem is not None:
                for abstract_text in abstract_elem.findall(".//AbstractText"):
                    label = abstract_text.get("Label", "")
                    text = "".join(abstract_text.itertext())
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

            # 作者
            authors = []
            author_list = article.find(".//AuthorList")
            if author_list is not None:
                for author in author_list.findall(".//Author"):
                    last_name = author.findtext("LastName", "")
                    fore_name = author.findtext("ForeName", "")
                    if last_name:
                        authors.append(f"{last_name} {fore_name}".strip())

            # 期刊資訊
            journal = article.find(".//Journal")
            journal_title = ""
            pub_date = ""
            if journal is not None:
                journal_title = journal.findtext(".//Title", "")
                if not journal_title:
                    journal_title = journal.findtext(".//ISOAbbreviation", "")

                pub_date_elem = journal.find(".//PubDate")
                if pub_date_elem is not None:
                    year = pub_date_elem.findtext("Year", "")
                    month = pub_date_elem.findtext("Month", "")
                    day = pub_date_elem.findtext("Day", "")
                    pub_date = f"{year} {month} {day}".strip()

            # 文章類型
            pub_types = []
            for pub_type in article.findall(".//PublicationType"):
                pub_types.append(pub_type.text)

            # 關鍵詞
            keywords = []
            keyword_list = medline.find(".//KeywordList")
            if keyword_list is not None:
                for kw in keyword_list.findall(".//Keyword"):
                    if kw.text:
                        keywords.append(kw.text)

            # MeSH 詞彙
            mesh_terms = []
            mesh_list = medline.find(".//MeshHeadingList")
            if mesh_list is not None:
                for mesh in mesh_list.findall(".//MeshHeading"):
                    descriptor = mesh.findtext(".//DescriptorName", "")
                    if descriptor:
                        mesh_terms.append(descriptor)

            # DOI
            doi = ""
            article_ids = article_elem.find(".//PubmedData/ArticleIdList")
            if article_ids is not None:
                for aid in article_ids.findall(".//ArticleId"):
                    if aid.get("IdType") == "doi":
                        doi = aid.text
                        break

            # 判斷是否為高品質期刊
            is_high_impact = any(
                hj.lower() in journal_title.lower()
                for hj in HIGH_IMPACT_JOURNALS
            )

            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal_title,
                "pub_date": pub_date,
                "pub_types": pub_types,
                "keywords": keywords,
                "mesh_terms": mesh_terms,
                "doi": doi,
                "is_high_impact": is_high_impact,
                "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "fetched_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"解析文章錯誤: {e}")
            return None

    def fetch_nephrology_articles(
        self,
        category: str = "all",
        max_results: int = DEFAULT_MAX_RESULTS,
        days_back: int = DEFAULT_DAYS_BACK,
        high_impact_only: bool = False
    ) -> dict:
        """
        獲取腎臟學文章

        Args:
            category: 類別 (all, pediatric_nephrology, adult_nephrology)
            max_results: 每個類別的最大結果數
            days_back: 搜尋過去幾天的文獻
            high_impact_only: 是否只返回高品質期刊的文章

        Returns:
            按類別組織的文章字典
        """
        results = {}

        categories = (
            list(SEARCH_QUERIES.keys())
            if category == "all"
            else [category]
        )

        for cat in categories:
            if cat not in SEARCH_QUERIES:
                continue

            query_info = SEARCH_QUERIES[cat]
            print(f"正在搜尋: {query_info['name']}...")

            # 搜尋文章
            pmids = self.search_articles(
                query_info["query"],
                max_results=max_results,
                days_back=days_back
            )

            print(f"找到 {len(pmids)} 篇文章")

            # 獲取詳細資訊
            if pmids:
                articles = self.fetch_article_details(pmids)

                # 過濾高品質期刊
                if high_impact_only:
                    articles = [a for a in articles if a.get("is_high_impact")]

                results[cat] = {
                    "name": query_info["name"],
                    "name_en": query_info["name_en"],
                    "topics": query_info["topics"],
                    "articles": articles,
                    "count": len(articles),
                    "search_date": datetime.now().isoformat(),
                    "days_back": days_back
                }

            # 避免過於頻繁的請求
            time.sleep(0.5)

        return results

    def save_articles(self, articles_data: dict, filepath: Optional[str] = None):
        """儲存文章資料到 JSON 檔案"""
        if filepath is None:
            os.makedirs(DATA_DIR, exist_ok=True)
            filepath = os.path.join(DATA_DIR, ARTICLES_FILE)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)

        print(f"文章已儲存至: {filepath}")

    def load_articles(self, filepath: Optional[str] = None) -> dict:
        """載入文章資料"""
        if filepath is None:
            filepath = os.path.join(DATA_DIR, ARTICLES_FILE)

        if not os.path.exists(filepath):
            return {}

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)


def main():
    """測試用主程式"""
    fetcher = PubMedFetcher()

    # 獲取最近 7 天的腎臟學文章
    results = fetcher.fetch_nephrology_articles(
        category="all",
        max_results=30,
        days_back=7
    )

    # 儲存結果
    fetcher.save_articles(results)

    # 顯示統計
    for cat, data in results.items():
        print(f"\n{data['name']}: {data['count']} 篇文章")
        for article in data["articles"][:3]:
            print(f"  - {article['title'][:60]}...")


if __name__ == "__main__":
    main()
