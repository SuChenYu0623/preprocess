import concurrent.futures
import requests
from pymongo import MongoClient
import hashlib

from captionService import CaptionService

def encrypt_src_md5(src, length=8):
    # 將 src 編碼後進行 MD5 雜湊
    hash_obj = hashlib.md5(src.encode('utf-8'))
    # 取得 32 字元的 hex digest，再取前 length 個字元
    code = hash_obj.hexdigest()[:length]
    return code


client = MongoClient("mongodb://localhost:27017/")
db = client["crawl_database"]
collection = db["crawl_items"]

# 獲取 image info list
query = {"downloaded": False}  # 篩選未爬取的資料
size = 20
cursor = collection.find(query, {"_id": 0, "newsId": 1, "images_with_desc": 1}).sort("postTime", 1).limit(size)

imageInfoList = []
for doc in cursor:
    newsId = doc["newsId"]
    images_with_desc = doc["images_with_desc"]

    for image_with_desc in images_with_desc:
        src = image_with_desc.get("src", None)
        alt = image_with_desc.get("alt", None)
        desc = image_with_desc.get("desc", None)
        caption = desc or alt 
        if not caption: continue

        encrypt_src = encrypt_src_md5(src)
        imageId = f'{newsId}_{encrypt_src}'
        imageInfo = { 
            "newsId": newsId, 
            "imageId": imageId, 
            "image": src,
            "caption": caption
        }
        imageInfoList.append(imageInfo)

print(imageInfoList)

# 下載 + 建立 caption.txt
def download_image(info):
    newsId = info["newsId"]
    imageId = info["imageId"]
    image_url = info["image"]
    caption = info["caption"]
    
    try:
        print(f"[{imageId}] 正在下載...")
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # 若 HTTP 請求返回錯誤則會引發例外
        
        # 設定檔案名稱 (這裡以 id 命名，副檔名可依實際圖片格式調整)
        file_name = f"source_images/{imageId}.jpg"
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 更新 mongo 
        print(f"[{imageId}] 下載完成！")
        captionService = CaptionService()
        if not captionService.existCaptionTxts():
            captionService.writeInitCaptionTxts()
        else:
            captionService.writeCaptionTxts(f'{imageId}.jpg', caption)

    except Exception as e:
        collection.update_one({"newsId": newsId}, {"$set": {"download": False}})
        print(f"[{imageId}] 下載時發生錯誤 or 寫 caption 時: {e}")


# 使用 ThreadPoolExecutor 進行多工下載
# max_workers 的數量可依實際需求調整
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # 將 imageInfoList 的每個元素都交由 download_image 處理
    executor.map(download_image, imageInfoList)
