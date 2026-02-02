# 腎臟學研究週報系統

自動從 PubMed 抓取最新高品質腎臟學臨床研究的 Streamlit 應用程式。

## 功能特色

### 自動文獻抓取
- 每週自動從 PubMed 抓取最新的腎臟學臨床研究
- 涵蓋 **兒童腎臟學** 和 **成人腎臟學** 兩大領域
- 專注於高品質研究：RCT、統合分析、系統性回顧、世代研究

### 智慧摘要
- 自動分析文獻並生成結構化摘要
- 識別高影響力期刊文章
- 提取關鍵結果和結論

### 研究趨勢分析
- 熱門研究主題識別
- 趨勢關鍵詞追蹤（治療方法、診斷技術、研究主題）
- MeSH 詞彙分析
- 期刊和文章類型分布

### 研究想法建議
- 基於趨勢分析提供研究建議
- 識別研究缺口和新興領域
- 跨領域研究機會
- 方法學創新建議

## 涵蓋領域

### 兒童腎臟學
- 急性腎損傷 (AKI)
- 慢性腎臟病 (CKD)
- 腎病症候群
- 腎絲球腎炎
- 先天性腎臟異常 (CAKUT)
- 血液透析/腹膜透析
- 腎臟移植
- 泌尿道感染
- 遺傳性腎臟病

### 成人腎臟學
- 急性腎損傷 (AKI)
- 慢性腎臟病 (CKD)
- 糖尿病腎病變
- 高血壓腎病變
- 腎絲球腎炎
- 血液透析/腹膜透析
- 腎臟移植
- 多囊腎
- 電解質異常

## 安裝與使用

### 環境需求
- Python 3.9+
- pip

### 安裝步驟

1. 安裝依賴套件
```bash
pip install -r requirements.txt
```

2. 執行應用程式
```bash
streamlit run streamlit_app.py
```

3. 在瀏覽器開啟 http://localhost:8501

### 手動抓取文獻
```bash
python fetch_weekly.py --days-back 7 --max-results 50
```

參數說明：
- `--days-back`: 搜尋過去幾天的文獻 (預設: 7)
- `--max-results`: 每類別最大文章數 (預設: 50)
- `--high-impact-only`: 僅抓取高影響力期刊文章
- `--output-dir`: 輸出目錄 (預設: data)

## 自動化 (GitHub Actions)

系統設定為每週一自動執行文獻抓取：
- 排程時間：每週一 UTC 08:00 (台灣時間下午 4:00)
- 可在 GitHub Actions 頁面手動觸發

### 設定 NCBI API Key (可選)
1. 前往 https://www.ncbi.nlm.nih.gov/account/settings/ 申請 API Key
2. 在 GitHub Repository Settings > Secrets 新增 `NCBI_API_KEY`
3. 有 API Key 可以增加請求頻率限制

## 檔案結構

```
├── streamlit_app.py      # Streamlit 主應用程式
├── pubmed_fetcher.py     # PubMed API 整合模組
├── research_analyzer.py  # 研究分析和摘要生成
├── config.py             # 配置設定
├── fetch_weekly.py       # 命令列抓取腳本
├── requirements.txt      # Python 依賴
├── data/                 # 資料儲存目錄
│   ├── articles.json     # 抓取的文章資料
│   ├── weekly_summary.json # 每週摘要
│   └── trends.json       # 趨勢分析
└── .github/
    └── workflows/
        └── weekly_fetch.yml  # GitHub Actions 自動化
```

## 高影響力期刊列表

系統追蹤以下高影響力期刊：
- N Engl J Med, Lancet, JAMA, BMJ
- J Am Soc Nephrol, Kidney Int
- Am J Kidney Dis, Clin J Am Soc Nephrol
- Nephrol Dial Transplant, Pediatr Nephrol
- Am J Transplant, Transplantation
- Nat Rev Nephrol, Kidney Int Rep
- 及其他知名醫學期刊

## 趨勢關鍵詞追蹤

### 治療方法
SGLT2 inhibitor, GLP-1, finerenone, dapagliflozin, empagliflozin, immunotherapy, gene therapy, stem cell, biologics

### 診斷技術
biomarker, machine learning, artificial intelligence, proteomics, metabolomics, genetic testing, digital health

### 研究主題
cardiovascular, heart failure, inflammation, fibrosis, oxidative stress, gut microbiome, precision medicine, telemedicine

### 臨床結局
mortality, hospitalization, quality of life, patient-reported outcomes, cost-effectiveness, eGFR decline, proteinuria, ESKD

## 授權

MIT License
