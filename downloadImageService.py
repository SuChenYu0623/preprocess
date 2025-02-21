'''
單次下載的動作 imageId, image_url
'''
import hashlib
import concurrent.futures
import requests
from pymongo import MongoClient

class DownloadImageService:
    def __init__(self):
        pass

    def encrypt_src_md5(self, src):
        # 將 src 編碼後進行 MD5 雜湊
        hash_obj = hashlib.md5(src.encode('utf-8'))
        # 取得 32 字元的 hex digest，再取前 length 個字元
        code = hash_obj.hexdigest()[:8]
        return code
    
    def downloadSingle(self, imageId, image_url):
        try:
            print(f"[{imageId}] 正在下載...")
            response = requests.get(image_url, stream=True)
            response.raise_for_status()  # 若 HTTP 請求返回錯誤則會引發例外

            file_name = f"source_images/{imageId}.jpg"
            with open(file_name, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
        except Exception as e:
            pass
            return False
        return True
