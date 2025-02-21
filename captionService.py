'''
檢查 caption.txt 是否存在
    否 建立初版
    是 寫入新的東西
'''

import os

class CaptionService:
    def __init__(self):
        self.file_name = 'caption.txt'
        pass

    def existCaptionTxts(self):
        return os.path.exists(self.file_name)

    def writeInitCaptionTxts(self):
        with open(self.file_name, 'x') as f:
            f.write('image,caption\n')
    
    def writeCaptionTxts(self, image, caption):
        with open(self.file_name, 'a') as f:
            f.write(f'{image},{caption}\n')
        