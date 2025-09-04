import concurrent.futures
import requests
from pymongo import MongoClient
import hashlib
import csv
from io import BytesIO
import requests
from PIL import Image
import time

setting = {
    "saveDataPath":
    "/home/chris/Desktop/crawlSystem/preprocess/newsDataset2",
    "saveImagePath":
    "/home/chris/Desktop/crawlSystem/preprocess/newsDataset2/images"
}


def is_valid_image_url(imageId, url, setting=setting):
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
                img.save(
                    f"{setting['saveImagePath']}/{imageId}.{file_extension}")
                # print("✅ 圖片下載成功且內容有效")
                # return True
                return f'{imageId}.{file_extension}'
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
        desc = image_with_desc.get("desc", None) or image_with_desc.get(
            "caption", None)

        encrypt_src = encrypt_src_md5(src)
        imageId = f'{newsId}_{encrypt_src}'

        image_name = is_valid_image_url(imageId=imageId, url=src)
        if src and image_name:
            if alt:
                imageInfo = parseImageInfo(image_name, alt, src, newsId)
                result.append(imageInfo)

            if desc:
                imageInfo = parseImageInfo(image_name, desc, src, newsId)
                result.append(imageInfo)

    # summary
    if summary and len(summary.split(' ')) < 50:
        imageInfo = parseImageInfo(imageId, summary, src, newsId)
        result.append(imageInfo)

    return result


client = MongoClient("mongodb://localhost:27017/")
db = client["crawl_database"]
collection = db["crawl_items"]
print('collection', collection)
query = {"downloaded": False}  # 篩選未爬取的資料
querySource = {"_id": 0, "newsId": 1, "images_with_desc": 1, "summary": 1}
size = 11000
cursor = collection.find(query, querySource,
                         no_cursor_timeout=True).sort("postTime",
                                                      1).limit(size)

docs = [doc for doc in cursor]
print(len(docs))

# imageInfoList = []
# # for idx, doc in enumerate(cursor):
# for idx, doc in enumerate(docs):
#     try:
#         if idx % 100 == 0:
#             print(f"idx: {idx}, total: {size}")
#         result = parseDocToImageInfo(doc)
#         imageInfoList += result  # 合併
#         time.sleep(5)
#     except Exception as e:
#         print(f'{idx}, {e}')

# print(len(imageInfoList))
# print(type(imageInfoList))

# # 寫入 csv
# fields = imageInfoList[0].keys()
# with open(f'{setting["saveDataPath"]}/captions.csv', 'w',
#           newline='') as csvfile:
#     writer = csv.DictWriter(csvfile, fieldnames=fields)
#     writer.writeheader()  # 寫入標題（欄位名稱）
#     writer.writerows(imageInfoList)  # 使用 writerows() 一次性將所有資料寫入

# print(f'CSV 檔案 list.csv 已成功建立。')
