from typing import Dict
import requests
from pymongo import MongoClient
import hashlib
import csv
from io import BytesIO
import requests
import time
from typing import List
from pydantic import BaseModel
from PIL import Image


class MongoSetting(BaseModel):
    mongo_host: str
    database_name: str
    collection_name: str
    query: Dict[str, int]
    projection: Dict[str, bool]
    size: int


class FolderSetting(BaseModel):
    caption_path: str
    image_path: str


class DownloadImageAndCreateCaptionService:

    def __init__(self, mongo_setting: MongoSetting,
                 folder_setting: FolderSetting):
        self.mongo_setting = mongo_setting
        self.folder_setting = folder_setting
        self.image_info_list = []  # 最終輸出

    def start(self):
        # connect db
        docs = self.conect_db_query_docs(mongo_setting=self.mongo_setting)

        # main download images & captions
        for idx, doc in enumerate(docs):
            try:
                if idx % 100 == 0 or idx == len(docs) - 1:
                    print(f"idx: {idx}, total: {self.mongo_setting.size}")
                result = self.parse_doc_to_image_info(doc)
                self.image_info_list += result  # 合併
                time.sleep(5)
            except Exception as e:
                print(f'{idx}, {e}')

        # main save cptions.csv
        self.save_captions_csv(caption_path=self.folder_setting.caption_path,
                               fields=self.image_info_list[0].keys(),
                               image_info_list=self.image_info_list)

    def conect_db_query_docs(self, mongo_setting: MongoSetting):
        client = MongoClient(mongo_setting.mongo_host)
        db = client[mongo_setting.database_name]
        collection = db[mongo_setting.collection_name]
        cursor = collection.find(mongo_setting.query,
                                 mongo_setting.projection).sort(
                                     "postTime", 1).limit(mongo_setting.size)
        docs = [doc for doc in cursor]
        print(f"doc共有 {len(docs)} 筆")
        return docs

    def is_valid_image_url(self, image_id: str, url: str, image_path: str):
        """
        確認 image url 是否正常
            - 正常: 下載
            - 異常: nothing
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0"  # 模擬正常瀏覽器請求
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200 and 'image' in response.headers.get(
                    'Content-Type', ''):
                try:
                    # 驗證圖片是否有效
                    img = Image.open(BytesIO(response.content))
                    img.verify()

                    # 重新打開，verify會破壞檔案指標
                    img = Image.open(BytesIO(response.content))
                    file_extension = img.format.lower()
                    img.save(f"{image_path}/{image_id}.{file_extension}")
                    return f'{image_id}.{file_extension}'
                except Exception as e:
                    print(f"⚠️ 圖片內容損壞或不是圖片：{e},  url: {url}")
                    return False
            else:
                print(
                    f"❌ 無效的圖片連結或 Content-Type 錯誤: {response.status_code}, {response.headers.get('Content-Type')}, url: {url}"
                )
                return False
        except requests.RequestException as e:
            print(f"🚫 網路錯誤：{e}, url: {url}")
            return False

    def encrypt_src_md5(self, src: str, length=8):
        """對src加密，縮短長度"""
        # 將 src 編碼後進行 MD5 雜湊
        hash_obj = hashlib.md5(src.encode('utf-8'))
        # 取得 32 字元的 hex digest，再取前 length 個字元
        code = hash_obj.hexdigest()[:length]
        return code

    def parse_image_info(self, image_id: str, caption: str, src: str,
                         newsId: str):
        """
        解析單一圖片描述
        """
        if not image_id: return
        if not caption: return
        if not src: return
        if not newsId: return
        return {
            "image": image_id,
            "caption": caption,
            "src": src,
            "newsId": newsId,
            "download": False
        }

    def parse_doc_to_image_info(self, doc):
        """
        解析單一篇新聞，但有多張圖片，甚至單一圖片多個描述的狀態
        """
        result = []
        newsId = doc["newsId"]
        summary = doc.get("summary", None)
        images_with_desc = doc["images_with_desc"]

        # 從 images_with_desc 拿
        for image_with_desc in images_with_desc:
            src = image_with_desc.get("src", None)
            alt = image_with_desc.get("alt", None)
            desc = image_with_desc.get("desc", None) or image_with_desc.get(
                "caption", None)

            encrypt_src = self.encrypt_src_md5(src)
            image_id = f'{newsId}_{encrypt_src}'

            image_name = self.is_valid_image_url(
                image_id=image_id,
                url=src,
                image_path=self.folder_setting.image_path)
            if src and image_name:
                if alt:
                    imageInfo = self.parse_image_info(image_name, alt, src,
                                                      newsId)
                    result.append(imageInfo)

                if desc:
                    imageInfo = self.parse_image_info(image_name, desc, src,
                                                      newsId)
                    result.append(imageInfo)

        # summary
        if summary and len(summary.split(' ')) < 50:
            imageInfo = self.parse_image_info(image_id, summary, src, newsId)
            result.append(imageInfo)

        return result

    def save_captions_csv(self, caption_path: str, fields: List[str],
                          image_info_list: List[Dict[str, str]]):
        with open(f'{caption_path}/captions.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()  # 寫入標題（欄位名稱）
            writer.writerows(image_info_list)


if __name__ == "__main__":
    MONGO_HOST = "mongodb://localhost:27017/"
    DATABASE_NAME = "crawl_database"
    COLLECTION_NAME = "crawl_items"
    QUERY = {}
    PROJECTION = {"_id": 0, "newsId": 1, "images_with_desc": 1, "summary": 1}
    SIZE = 3
    mongo_setting = {
        "mongo_host": MONGO_HOST,
        "database_name": DATABASE_NAME,
        "collection_name": COLLECTION_NAME,
        "query": QUERY,
        "projection": PROJECTION,
        "size": SIZE
    }
    folder_setting = {
        "caption_path": "/home/chris/Desktop/crawlSystem/preprocess/myData/",
        "image_path":
        "/home/chris/Desktop/crawlSystem/preprocess/myData/images"
    }
    service = DownloadImageAndCreateCaptionService(
        mongo_setting=MongoSetting(**mongo_setting),
        folder_setting=FolderSetting(**folder_setting))
    service.start()
