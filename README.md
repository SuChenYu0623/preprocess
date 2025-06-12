# 下載圖片並產生描述服務

一個 Python 工具，從 MongoDB 讀取圖片中繼資料，下載並驗證圖片，最後匯出 captions.csv，方便後續訓練或資料分析使用。

## 特色
- MongoDB 整合：可自訂查詢條件與投影欄位。
- 圖片驗證：使用 Pillow 檢查並確保下載內容為有效圖片。
- 描述蒐集：自動彙整文件中的 alt、desc、caption 以及文章 summary。
- CSV 匯出：產生乾淨的 captions.csv，直接可用於訓練或標註。

## 專案結構
```
.
└── preprocess/
    ├── requirements.txt
    ├── README.md       
    ├── main.py           # 主程式
    └── myData/
        ├── captions.csv  # 執行後產生
        └── images/       # 下載的圖片
```

## 快速開始
```
# 1. git clone
git clone <本篇 ssh.git>

# 2. 建立虛擬環境 & 安裝套件
python3 -m venv venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. run
python main.py
```

## 設定
程式透過兩個 `pydantic` 模型讀取參數：
```
class MongoSetting(BaseModel):
    mongo_host: str                # 例如 "mongodb://localhost:27017/"
    database_name: str             # 例如 "crawl_database"
    collection_name: str           # 例如 "crawl_items"
    query: Dict[str, int]          # Mongo 查詢條件（{} 代表全部）
    projection: Dict[str, bool]    # 欄位投影
    size: int                      # 要處理的文件數上限

class FolderSetting(BaseModel):
    caption_path: str              # captions.csv 存放目錄
    image_path: str                # 圖片下載目錄
```

## 授權
MIT，詳見 LICENSE。
