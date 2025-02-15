import concurrent.futures
import requests


# datas
imageInfoList = [
    {
        "newsId": "a1",
        "image": "https://www.tohome.com/images/Products/500/10012017/F4U047bt.jpg"
    },
    {
        "newsId": "a2",
        "image": "https://www.tohome.com/images/Products/500/13062017/Asus-320M.jpg"
    },
]

def download_image(info):
    newsId = info["newsId"]
    image_url = info["image"]
    
    try:
        print(f"[{newsId}] 正在下載...")
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # 若 HTTP 請求返回錯誤則會引發例外
        
        # 設定檔案名稱 (這裡以 id 命名，副檔名可依實際圖片格式調整)
        file_name = f"source_images/{newsId}.jpg"
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[{newsId}] 下載完成！")
    except Exception as e:
        print(f"[{newsId}] 下載時發生錯誤: {e}")


# 使用 ThreadPoolExecutor 進行多工下載
# max_workers 的數量可依實際需求調整
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # 將 imageInfoList 的每個元素都交由 download_image 處理
    executor.map(download_image, imageInfoList)
