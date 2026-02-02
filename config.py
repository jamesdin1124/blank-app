"""
PubMed 腎臟學研究摘要系統配置
"""

# PubMed API 設定
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_SEARCH_URL = f"{PUBMED_BASE_URL}/esearch.fcgi"
PUBMED_FETCH_URL = f"{PUBMED_BASE_URL}/efetch.fcgi"
PUBMED_SUMMARY_URL = f"{PUBMED_BASE_URL}/esummary.fcgi"

# 搜尋策略 - 高品質臨床研究
SEARCH_QUERIES = {
    "pediatric_nephrology": {
        "name": "兒童腎臟學",
        "name_en": "Pediatric Nephrology",
        "query": """
            (pediatric nephrology[MeSH Terms] OR
             child kidney disease[Title/Abstract] OR
             pediatric kidney[Title/Abstract] OR
             childhood nephropathy[Title/Abstract] OR
             pediatric renal[Title/Abstract] OR
             children kidney[Title/Abstract] OR
             neonatal kidney[Title/Abstract] OR
             adolescent nephrology[Title/Abstract])
            AND
            (clinical trial[Publication Type] OR
             randomized controlled trial[Publication Type] OR
             meta-analysis[Publication Type] OR
             systematic review[Publication Type] OR
             cohort study[Title/Abstract] OR
             prospective study[Title/Abstract] OR
             multicenter study[Title/Abstract])
        """,
        "topics": [
            "急性腎損傷 (AKI)",
            "慢性腎臟病 (CKD)",
            "腎病症候群",
            "腎絲球腎炎",
            "先天性腎臟異常 (CAKUT)",
            "血液透析/腹膜透析",
            "腎臟移植",
            "泌尿道感染",
            "遺傳性腎臟病",
            "高血壓與腎臟"
        ]
    },
    "adult_nephrology": {
        "name": "成人腎臟學",
        "name_en": "Adult Nephrology",
        "query": """
            (nephrology[MeSH Terms] OR
             kidney disease[MeSH Terms] OR
             renal insufficiency[MeSH Terms] OR
             chronic kidney disease[Title/Abstract] OR
             acute kidney injury[Title/Abstract] OR
             glomerulonephritis[Title/Abstract] OR
             dialysis[Title/Abstract] OR
             kidney transplantation[Title/Abstract])
            NOT
            (pediatric[Title/Abstract] OR
             children[Title/Abstract] OR
             child[Title/Abstract] OR
             neonatal[Title/Abstract] OR
             adolescent[Title/Abstract])
            AND
            (clinical trial[Publication Type] OR
             randomized controlled trial[Publication Type] OR
             meta-analysis[Publication Type] OR
             systematic review[Publication Type] OR
             cohort study[Title/Abstract] OR
             prospective study[Title/Abstract] OR
             multicenter study[Title/Abstract])
            AND adult[MeSH Terms]
        """,
        "topics": [
            "急性腎損傷 (AKI)",
            "慢性腎臟病 (CKD)",
            "糖尿病腎病變",
            "高血壓腎病變",
            "腎絲球腎炎",
            "血液透析",
            "腹膜透析",
            "腎臟移植",
            "多囊腎",
            "電解質異常",
            "腎臟腫瘤"
        ]
    }
}

# 高品質期刊列表 (Impact Factor 較高的腎臟學相關期刊)
HIGH_IMPACT_JOURNALS = [
    "N Engl J Med",
    "Lancet",
    "JAMA",
    "BMJ",
    "Ann Intern Med",
    "J Am Soc Nephrol",
    "Kidney Int",
    "Am J Kidney Dis",
    "Clin J Am Soc Nephrol",
    "Nephrol Dial Transplant",
    "Pediatr Nephrol",
    "Am J Transplant",
    "Transplantation",
    "Nat Rev Nephrol",
    "Kidney Int Rep",
    "J Clin Invest",
    "JAMA Intern Med",
    "JAMA Pediatr",
    "Pediatrics",
    "J Pediatr"
]

# 搜尋參數
DEFAULT_MAX_RESULTS = 50  # 每次搜尋最大結果數
DEFAULT_DAYS_BACK = 7     # 預設搜尋過去幾天的文獻

# 研究趨勢關鍵詞
TREND_KEYWORDS = {
    "治療方法": [
        "SGLT2 inhibitor", "GLP-1", "finerenone", "dapagliflozin",
        "empagliflozin", "canagliflozin", "immunotherapy",
        "gene therapy", "stem cell", "biologics"
    ],
    "診斷技術": [
        "biomarker", "machine learning", "artificial intelligence",
        "proteomics", "metabolomics", "genetic testing",
        "point-of-care", "digital health"
    ],
    "研究主題": [
        "cardiovascular", "heart failure", "inflammation",
        "fibrosis", "oxidative stress", "gut microbiome",
        "precision medicine", "personalized", "telemedicine"
    ],
    "臨床結局": [
        "mortality", "hospitalization", "quality of life",
        "patient-reported outcomes", "cost-effectiveness",
        "eGFR decline", "proteinuria", "ESKD"
    ]
}

# 資料儲存路徑
DATA_DIR = "data"
ARTICLES_FILE = "articles.json"
SUMMARY_FILE = "weekly_summary.json"
TRENDS_FILE = "trends.json"
