import concurrent.futures
import requests
from pymongo import MongoClient
import hashlib
import csv

def encrypt_src_md5(src, length=8):
    # 將 src 編碼後進行 MD5 雜湊
    hash_obj = hashlib.md5(src.encode('utf-8'))
    # 取得 32 字元的 hex digest，再取前 length 個字元
    code = hash_obj.hexdigest()[:length]
    return code

def parseImageInfo(imageId, caption, src, newsId):
    if not imageId: return
    if not caption: return
    if not src: return
    if not newsId: return
    return {
        "image": imageId,
        "caption": caption,
        "src": src,
        "newsId": newsId,
        "download": False
    }

def parseDocToImageInfo(doc):
    result = []
    newsId = doc["newsId"]
    summary = doc.get("summary", None)
    images_with_desc = doc["images_with_desc"]

    # 從 images_with_desc 拿
    for image_with_desc in images_with_desc:
        src = image_with_desc.get("src", None)
        alt = image_with_desc.get("alt", None)
        desc = image_with_desc.get("desc", None) or image_with_desc.get("caption", None)
        
        encrypt_src = encrypt_src_md5(src)
        imageId = f'{newsId}_{encrypt_src}'
        
        if src:
            if alt:
                imageInfo = parseImageInfo(imageId, alt, src, newsId)
                result.append(imageInfo)
            
            if desc:
                imageInfo = parseImageInfo(imageId, desc, src, newsId)
                result.append(imageInfo)
    
    # summary
    if summary and len(summary.split(' ')) < 50:
        imageInfo = parseImageInfo(imageId, summary, src, newsId)
        result.append(imageInfo)

    return result

client = MongoClient("mongodb://localhost:27017/")
db = client["crawl_database"]
collection = db["crawl_items"]

query = {"downloaded": False}  # 篩選未爬取的資料
size = 3900
cursor = collection.find(query, {"_id": 0, "newsId": 1, "images_with_desc": 1, "summary": 1}).sort("postTime", 1).limit(size)

imageInfoList = []
for doc in cursor:
    result = parseDocToImageInfo(doc)
    imageInfoList += result # 合併

print(len(imageInfoList))
print(type(imageInfoList))

# 寫入 csv
fields = imageInfoList[0].keys()
with open('list.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader() # 寫入標題（欄位名稱）
    writer.writerows(imageInfoList) # 使用 writerows() 一次性將所有資料寫入

print(f'CSV 檔案 list.csv 已成功建立。')