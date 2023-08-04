import ctypes
from ctypes import *
import time
from src.common import config
from src.common.usb import USB

class DllLoader:

    @staticmethod
    def load():
        config.dllTool = DllLoader()
        config.usb = USB()
        config.usb.load()
    
    def __init__(self):
        self.dll = cdll.LoadLibrary('./MarsDLL.dll')
        config.dllTool = self

    def screenSearch(self, str_path):
        path = str_path.encode('utf-8')
        # image = dll.dloadImage(path, 0, 0, 0, 0)
        ImageSearch = self.dll.ImageSearch
        ImageSearch.restype = ctypes.c_char_p
        start_time = time.time()
        result = self.dll.ImageSearch(0,0,1024,768,path,0)
        end_time = time.time()
        print("耗时: {:.2f}秒".format(end_time - start_time))
        array_result = str(result).split('|', -1)
        if len(array_result) == 5:
            return int(array_result[1]), int(array_result[2])
        else:
            return -1, -1

if __name__ == '__main__':
    load = DllLoader()
    resut = load.screenSearch("./assets/minimap_me.bmp")
    print(resut)

    
