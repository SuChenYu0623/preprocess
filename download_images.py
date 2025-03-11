import concurrent.futures
import requests
import pandas as pd
import os
from ratelimiter import RateLimiter

image_folder = 'image_list'
csv_file = 'list.csv'

# 設定每秒最多 2 次請求
rate_limiter = RateLimiter(max_calls=100, period=60)

@rate_limiter
def download_image(imageInfo): # # 下載 + 建立 caption.txt
    imageId = imageInfo[0] 
    imageUrl = imageInfo[1]
    try:
        print(f"[{imageUrl}] 正在下載...")
        response = requests.get(imageUrl, stream=True)
        response.raise_for_status()  # 若 HTTP 請求返回錯誤則會引發例外
        
        # 設定檔案名稱 (這裡以 id 命名，副檔名可依實際圖片格式調整)
        # file_name = f"{image_folder}/{imageId}.jpg"
        file_name = os.path.join(image_folder, f"{imageId}.jpg")
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[{imageId}] 下載完成！")
    except Exception as e:
        print(f"[{imageId}] 下載時發生錯誤 or 寫 caption 時: {e}")


# ------------------

df = pd.read_csv(csv_file)
imageUrls = df['src'].values
imageIds = df['image'].values
# print('imageIds', len(imageIds))
# print('imageUrls', len(imageUrls))

# 12290 ids
# 11973
df_filtered = df.drop_duplicates(subset='image')
imageInfoList = df_filtered[['image', 'src']].values
print('imageInfoList', len(imageInfoList))


# 使用 ThreadPoolExecutor 進行多工下載
# max_workers 的數量可依實際需求調整
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # 將 imageInfoList 的每個元素都交由 download_image 處理
    executor.map(download_image, imageInfoList)


