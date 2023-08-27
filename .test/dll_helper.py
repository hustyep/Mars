import ctypes
from ctypes import *
from ctypes import wintypes
import time
import threading

class DllHelper:
    
    def __init__(self):
        self.dll = cdll.LoadLibrary('./MarsDLL.dll')
        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        print('\n[~] Started load dll')
        self.thread.start()

    def _main(self):
        self.ready = True

    def screenSearch(self, bitmap_template, x, y, width, height, path_template=None, frame=None):
        if path_template:
            path = path_template.encode('utf-8')
        else:
            path = None
        ImageSearch = self.dll.ImageSearch
        ImageSearch.restype = ctypes.c_char_p
        ImageSearch.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_char_p,wintypes.HBITMAP,wintypes.HBITMAP]
        start_time = time.time()
        result = ImageSearch(x,y,width,height,path,frame,bitmap_template)
        end_time = time.time()
        print("耗时: {:.4f}秒".format(end_time - start_time))
        array_result = str(result).split('|', -1)
        if len(array_result) == 5:
            return int(array_result[1]), int(array_result[2])
        else:
            return -1, -1
        
    def loadImage(self, str_path):
        dloadImage = self.dll.dloadImage
        dloadImage.restype = wintypes.HBITMAP
        path = str_path.encode('utf-8')
        image = self.dll.dloadImage(path, 0, 0, 0, 0)
        return image

dll_helper = DllHelper()

if __name__ == '__main__':
    # resut = load.screenSearch("./assets/minimap_me.bmp")
    template = dll_helper.loadImage('assets/big_mouse_template.png')
    frame = dll_helper.loadImage(".test/Maple_230819_152709.png")
    result = dll_helper.screenSearch(template,frame=frame)
    print(result)

    
