"""
腎臟學研究摘要系統 - Streamlit 應用程式
每週自動從 PubMed 抓取最新的高品質腎臟學臨床研究
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd

from pubmed_fetcher import PubMedFetcher
from research_analyzer import ResearchAnalyzer
from config import DATA_DIR, ARTICLES_FILE, SUMMARY_FILE, TRENDS_FILE

# 頁面配置
st.set_page_config(
    page_title="腎臟學研究週報",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .article-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .high-impact-badge {
        background-color: #FFD700;
        color: #333;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .idea-card {
        background-color: #e8f4ea;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 10px 10px 0;
    }
    .trend-tag {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


def load_cached_data():
    """載入快取的資料"""
    articles_path = os.path.join(DATA_DIR, ARTICLES_FILE)
    summary_path = os.path.join(DATA_DIR, SUMMARY_FILE)
    trends_path = os.path.join(DATA_DIR, TRENDS_FILE)

    articles = {}
    summary = {}
    trends = {}

    if os.path.exists(articles_path):
        with open(articles_path, "r", encoding="utf-8") as f:
            articles = json.load(f)

    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    if os.path.exists(trends_path):
        with open(trends_path, "r", encoding="utf-8") as f:
            trends = json.load(f)

    return articles, summary, trends


def fetch_new_articles(days_back: int, max_results: int, high_impact_only: bool):
    """抓取新文章"""
    with st.spinner("正在從 PubMed 抓取最新文獻..."):
        fetcher = PubMedFetcher()
        articles = fetcher.fetch_nephrology_articles(
            category="all",
            max_results=max_results,
            days_back=days_back,
            high_impact_only=high_impact_only
        )
        fetcher.save_articles(articles)

        # 分析並生成摘要
        analyzer = ResearchAnalyzer(articles)
        trends = analyzer.analyze_trends()
        analyzer.save_trends(trends)

        summary = analyzer.generate_weekly_summary()
        analyzer.save_summary(summary)

        return articles, summary, trends


def render_sidebar():
    """渲染側邊欄"""
    st.sidebar.markdown("## 控制面板")

    # 搜尋設定
    st.sidebar.markdown("### 搜尋設定")
    days_back = st.sidebar.slider("搜尋天數", 1, 30, 7)
    max_results = st.sidebar.slider("每類別最大文章數", 10, 100, 50)
    high_impact_only = st.sidebar.checkbox("僅高影響力期刊", False)

    # 抓取按鈕
    if st.sidebar.button("抓取最新文獻", type="primary", use_container_width=True):
        articles, summary, trends = fetch_new_articles(days_back, max_results, high_impact_only)
        st.sidebar.success(f"成功抓取 {summary.get('執行摘要', {}).get('總文章數', 0)} 篇文章！")
        st.rerun()

    # 顯示上次更新時間
    articles, summary, _ = load_cached_data()
    if summary:
        report_date = summary.get("報告日期", "")
        if report_date:
            try:
                dt = datetime.fromisoformat(report_date)
                st.sidebar.info(f"上次更新: {dt.strftime('%Y-%m-%d %H:%M')}")
            except (ValueError, TypeError):
                pass

    # 篩選選項
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 篩選選項")

    categories = ["全部"]
    if articles:
        categories.extend([data.get("name", cat) for cat, data in articles.items()])

    selected_category = st.sidebar.selectbox("類別", categories)

    return selected_category


def render_executive_summary(summary: dict):
    """渲染執行摘要"""
    st.markdown('<p class="main-header">腎臟學研究週報</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">自動追蹤最新高品質腎臟學臨床研究</p>', unsafe_allow_html=True)

    exec_summary = summary.get("執行摘要", {})

    # 關鍵指標
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("總文章數", exec_summary.get("總文章數", 0))

    with col2:
        st.metric("高影響力期刊", exec_summary.get("高影響力期刊文章數", 0))

    with col3:
        category_stats = summary.get("分類統計", {})
        pediatric_count = category_stats.get("兒童腎臟學", {}).get("文章數", 0)
        st.metric("兒童腎臟學", pediatric_count)

    with col4:
        adult_count = category_stats.get("成人腎臟學", {}).get("文章數", 0)
        st.metric("成人腎臟學", adult_count)

    # 主要發現
    findings = exec_summary.get("主要發現", [])
    if findings:
        st.markdown("### 本週重點發現")
        for finding in findings:
            st.markdown(f"- {finding}")


def render_trends(summary: dict, trends: dict):
    """渲染研究趨勢"""
    st.markdown("## 研究趨勢分析")

    research_trends = summary.get("研究趨勢", {})

    col1, col2 = st.columns(2)

    with col1:
        # 熱門主題
        st.markdown("### 熱門研究主題")
        hot_topics = research_trends.get("熱門主題", [])
        if hot_topics:
            df = pd.DataFrame(hot_topics, columns=["主題", "文章數"])
            st.bar_chart(df.set_index("主題"))

    with col2:
        # 期刊分布
        st.markdown("### 期刊分布")
        journal_dist = research_trends.get("期刊分布", {})
        if journal_dist:
            df = pd.DataFrame(list(journal_dist.items()), columns=["期刊", "文章數"])
            df = df.sort_values("文章數", ascending=True).tail(10)
            st.bar_chart(df.set_index("期刊"))

    # 趨勢關鍵詞
    st.markdown("### 趨勢關鍵詞")
    keyword_stats = research_trends.get("趨勢關鍵詞", {})

    if keyword_stats:
        tabs = st.tabs(list(keyword_stats.keys()))
        for tab, (category, keywords) in zip(tabs, keyword_stats.items()):
            with tab:
                if keywords:
                    # 顯示關鍵詞標籤
                    tags_html = ""
                    for kw, count in list(keywords.items())[:15]:
                        tags_html += f'<span class="trend-tag">{kw} ({count})</span> '
                    st.markdown(tags_html, unsafe_allow_html=True)
                else:
                    st.info("本週無相關關鍵詞")

    # 文章類型分布
    st.markdown("### 文章類型分布")
    pub_types = research_trends.get("文章類型", {})
    if pub_types:
        col1, col2 = st.columns([2, 1])
        with col1:
            df = pd.DataFrame(list(pub_types.items()), columns=["類型", "數量"])
            st.dataframe(df, use_container_width=True, hide_index=True)


def render_featured_articles(summary: dict, selected_category: str):
    """渲染重點文章"""
    st.markdown("## 重點文章")

    featured = summary.get("重點文章", [])

    if not featured:
        st.info("目前沒有文章資料。請點擊側邊欄的「抓取最新文獻」按鈕。")
        return

    # 篩選類別
    if selected_category != "全部":
        featured = [a for a in featured if selected_category in str(a)]

    for article in featured:
        with st.container():
            # 文章標題
            title = article.get("標題", "無標題")
            is_high_impact = article.get("是否高影響力期刊", False)

            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"#### {title}")
            with col2:
                if is_high_impact:
                    st.markdown('<span class="high-impact-badge">高影響力期刊</span>', unsafe_allow_html=True)

            # 文章資訊
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**期刊:** {article.get('期刊', 'N/A')}")
            with col2:
                st.markdown(f"**研究類型:** {article.get('研究類型', 'N/A')}")
            with col3:
                st.markdown(f"**發表日期:** {article.get('發表日期', 'N/A')}")

            # 摘要
            structured_abstract = article.get("結構化摘要", {})
            if structured_abstract:
                with st.expander("查看摘要"):
                    for section, content in structured_abstract.items():
                        st.markdown(f"**{section}:** {content}")

            # 相關趨勢
            related_trends = article.get("相關趨勢", [])
            if related_trends:
                trends_html = " ".join([f'<span class="trend-tag">{t}</span>' for t in related_trends])
                st.markdown(f"**相關趨勢:** {trends_html}", unsafe_allow_html=True)

            # 連結
            col1, col2 = st.columns(2)
            with col1:
                pubmed_url = article.get("PubMed連結", "")
                if pubmed_url:
                    st.markdown(f"[在 PubMed 查看]({pubmed_url})")
            with col2:
                doi = article.get("DOI", "")
                if doi:
                    st.markdown(f"[DOI: {doi}](https://doi.org/{doi})")

            st.markdown("---")


def render_research_ideas(summary: dict):
    """渲染研究想法"""
    st.markdown("## 研究想法與建議")

    ideas = summary.get("研究想法", [])

    if not ideas:
        st.info("分析資料後將生成研究想法建議。")
        return

    # 按類型分組
    idea_types = {}
    for idea in ideas:
        idea_type = idea.get("類型", "其他")
        if idea_type not in idea_types:
            idea_types[idea_type] = []
        idea_types[idea_type].append(idea)

    tabs = st.tabs(list(idea_types.keys()))

    for tab, (idea_type, type_ideas) in zip(tabs, idea_types.items()):
        with tab:
            for idea in type_ideas:
                st.markdown(f"""
                <div class="idea-card">
                    <strong>{idea.get('關鍵詞', '')}</strong>
                    <br><br>
                    {idea.get('想法', '').replace(chr(10), '<br>')}
                    <br><br>
                    <em>建議研究類型: {idea.get('建議研究類型', 'N/A')}</em>
                </div>
                """, unsafe_allow_html=True)


def render_mesh_analysis(summary: dict):
    """渲染 MeSH 詞彙分析"""
    st.markdown("## MeSH 詞彙分析")

    mesh_terms = summary.get("MeSH詞彙分析", {})

    if not mesh_terms:
        st.info("無 MeSH 詞彙資料。")
        return

    # 顯示前30個詞彙
    col1, col2 = st.columns(2)

    items = list(mesh_terms.items())
    half = len(items) // 2

    with col1:
        df1 = pd.DataFrame(items[:half], columns=["MeSH 詞彙", "頻率"])
        st.dataframe(df1, use_container_width=True, hide_index=True)

    with col2:
        df2 = pd.DataFrame(items[half:], columns=["MeSH 詞彙", "頻率"])
        st.dataframe(df2, use_container_width=True, hide_index=True)


def render_all_articles(articles: dict, selected_category: str):
    """渲染所有文章列表"""
    st.markdown("## 完整文章列表")

    all_articles = []
    for cat, data in articles.items():
        cat_name = data.get("name", cat)
        for article in data.get("articles", []):
            article["類別"] = cat_name
            all_articles.append(article)

    if not all_articles:
        st.info("目前沒有文章資料。")
        return

    # 篩選
    if selected_category != "全部":
        all_articles = [a for a in all_articles if a.get("類別") == selected_category]

    # 轉換為 DataFrame
    df = pd.DataFrame([
        {
            "標題": a.get("title", "")[:80] + "..." if len(a.get("title", "")) > 80 else a.get("title", ""),
            "期刊": a.get("journal", ""),
            "類別": a.get("類別", ""),
            "高影響力": "是" if a.get("is_high_impact") else "否",
            "發表日期": a.get("pub_date", ""),
            "PMID": a.get("pmid", "")
        }
        for a in all_articles
    ])

    # 搜尋功能
    search_term = st.text_input("搜尋文章標題", "")
    if search_term:
        df = df[df["標題"].str.contains(search_term, case=False, na=False)]

    st.dataframe(df, use_container_width=True, hide_index=True)

    # 下載功能
    if all_articles:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="下載文章列表 (CSV)",
            data=csv,
            file_name=f"nephrology_articles_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


def main():
    """主程式"""
    # 確保資料目錄存在
    os.makedirs(DATA_DIR, exist_ok=True)

    # 渲染側邊欄
    selected_category = render_sidebar()

    # 載入資料
    articles, summary, trends = load_cached_data()

    # 主要內容區域
    if summary:
        # 建立頁籤
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "執行摘要",
            "研究趨勢",
            "重點文章",
            "研究想法",
            "完整列表"
        ])

        with tab1:
            render_executive_summary(summary)

        with tab2:
            render_trends(summary, trends)

        with tab3:
            render_featured_articles(summary, selected_category)

        with tab4:
            render_research_ideas(summary)
            st.markdown("---")
            render_mesh_analysis(summary)

        with tab5:
            render_all_articles(articles, selected_category)

    else:
        # 首次使用，顯示歡迎訊息
        st.markdown('<p class="main-header">腎臟學研究週報</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">自動追蹤最新高品質腎臟學臨床研究</p>', unsafe_allow_html=True)

        st.markdown("""
        ### 歡迎使用腎臟學研究週報系統！

        本系統自動從 PubMed 抓取最新的高品質腎臟學臨床研究，包括：

        - **兒童腎臟學** - 急性腎損傷、慢性腎臟病、腎病症候群、先天性腎臟異常等
        - **成人腎臟學** - 糖尿病腎病變、高血壓腎病變、透析、腎臟移植等

        #### 主要功能：
        1. **自動抓取** - 每週自動從 PubMed 抓取最新文獻
        2. **智慧摘要** - 自動分析文獻並生成結構化摘要
        3. **趨勢分析** - 識別研究熱點和趨勢關鍵詞
        4. **研究想法** - 基於趨勢分析提供研究建議

        #### 開始使用：
        請點擊左側的 **「抓取最新文獻」** 按鈕開始抓取資料。
        """)

        # 顯示系統說明
        with st.expander("系統設定說明"):
            st.markdown("""
            **搜尋設定：**
            - **搜尋天數**: 設定要搜尋過去幾天的文獻 (1-30天)
            - **每類別最大文章數**: 設定每個類別最多抓取幾篇文章
            - **僅高影響力期刊**: 勾選後只顯示發表在高影響力期刊的文章

            **高影響力期刊包括：**
            - N Engl J Med, Lancet, JAMA, BMJ
            - J Am Soc Nephrol, Kidney Int, Am J Kidney Dis
            - Clin J Am Soc Nephrol, Pediatr Nephrol
            - 等知名腎臟學及醫學期刊
            """)


if __name__ == "__main__":
    main()
