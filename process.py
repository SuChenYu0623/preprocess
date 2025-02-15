import os
from PIL import Image
import concurrent.futures


def resize_and_crop(img, target_size):
    """
    裁剪模式：等比例縮放使圖片覆蓋目標尺寸，再從中間裁剪到目標大小。
    """
    target_w, target_h = target_size
    orig_w, orig_h = img.size
    # 計算縮放因子，取較大者，保證圖片至少覆蓋目標尺寸
    scale = max(target_w / orig_w, target_h / orig_h)
    new_size = (int(orig_w * scale), int(orig_h * scale))
    img = img.resize(new_size, Image.ANTIALIAS)
    
    # 以中心為基準裁剪
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    right = left + target_w
    bottom = top + target_h
    img = img.crop((left, top, right, bottom))
    return img

def resize_and_pad(img, target_size, color=(0, 0, 0)):
    """
    補邊模式：等比例縮放使圖片完整適應目標尺寸，然後補上背景色使圖片尺寸達到目標大小。
    """
    target_w, target_h = target_size
    orig_w, orig_h = img.size
    # 計算縮放因子，取較小者，保證整張圖片都能顯示在目標尺寸中
    scale = min(target_w / orig_w, target_h / orig_h)
    new_size = (int(orig_w * scale), int(orig_h * scale))
    img = img.resize(new_size, Image.ANTIALIAS)
    
    # 建立一個目標尺寸的背景圖（預設黑色）
    new_img = Image.new("RGB", target_size, color)
    # 將縮放後的圖片置中貼上
    left = (target_w - img.width) // 2
    top = (target_h - img.height) // 2
    new_img.paste(img, (left, top))
    return new_img

def process_image(file_name, source_dir, output_dir, target_size=(256, 256), mode="crop"):
    """
    處理單一圖片：
      1. 從 source_dir 讀取圖片
      2. 依照 mode 進行等比例縮放 + 裁剪或補邊
      3. 將處理後的圖片存到 output_dir
    """
    input_path = os.path.join(source_dir, file_name)
    output_path = os.path.join(output_dir, file_name)
    try:
        with Image.open(input_path) as img:
            # 確保圖片為 RGB 格式（有些圖片可能是 RGBA 或灰階）
            img = img.convert("RGB")
            if mode == "crop":
                processed_img = resize_and_crop(img, target_size)
            elif mode == "pad":
                processed_img = resize_and_pad(img, target_size)
            else:
                raise ValueError("mode 必須設定為 'crop' 或 'pad'")
            
            processed_img.save(output_path)
            print(f"{file_name} 處理完成並儲存到 {output_path}")
    except Exception as e:
        print(f"處理 {file_name} 時發生錯誤: {e}")

def main():
    # 設定來源與目標資料夾
    source_dir = "source_images"
    output_dir = "processed_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # 設定目標尺寸，例如 256x256
    target_size = (224, 224)
    # 設定處理模式，"crop" 為裁剪模式，"pad" 為補邊模式
    mode = "crop"  # 或改成 "pad"
    
    # 取得所有圖片檔案（這裡只讀取副檔名為 jpg、jpeg、png 的檔案）
    files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"總共發現 {len(files)} 個圖片檔案，開始處理...")
    
    # 使用多工處理，這裡採用 ProcessPoolExecutor（適用於 CPU 密集型工作）
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(process_image, file_name, source_dir, output_dir, target_size, mode)
            for file_name in files
        ]
        # 等待所有工作完成（如有需要也可以檢查 future.result()）
        for future in concurrent.futures.as_completed(futures):
            # 未取回結果僅為等待執行完成
            _ = future.result()

if __name__ == '__main__':
    main()