import ctypes
from ctypes import *
from src.common.common import singleton

# 字符串命令接口
# https://note.youdao.com/s/Gyrcngxs

# 键盘按键CMD
CMD_KEYBOARD_PRESS = "key:press"
CMD_KEYBOARD_UP = "key:up"
CMD_KEYBOARD_DOWN = "key:down"
CMD_KEYBOARD_HID = "key:hid"
CMD_KEYBOARD_STRING = "key:string"
CMD_KEYBOARD_RELEASE = "key:release"

#鼠标CMD
CMD_MOUSE_LEFT_CLICK = "mouse:leftclick"
CMD_MOUSE_LEFT_DOWN = "mouse:leftdown"
CMD_MOUSE_LEFT_UP = "mouse:leftup"
CMD_MOUSE_RIGHT_CLICK = "mouse:rightclick"
CMD_MOUSE_RIGHT_DOWN = "mouse:rightdown"
CMD_MOUSE_RIGHT_UP = "mouse:rightup"
CMD_MOUSE_MOVE = "mouse:move"
CMD_MOUSE_ABS_MOVE = "mouse:absmove"

# 多媒体
CMD_CONSUMER_SLEEP = "consumer:powersleep"

@singleton
class USB:
    dll = None
    usbopen = False

    def load(self):
        self.dll = cdll.LoadLibrary('./hiddll.dll')
        
        # 网络版硬件WIFIHID要和运行本脚本的电脑在同一局域网  USB版硬件要注释掉这两行
        # IP=ctypes.create_string_buffer(b'192.168.119.255')
        # dll.netcfg(IP,9000) # IP（可用广播地址） 端口

        # print("dll调用测试")
        # nRst  =  self.dll.test( )

        # USB版本硬件
        self.usbopen = self.dll.open_hiddev_default()
        if (self.usbopen < 0):
            print("USB硬件未连接")
        
        self.key_release()

    def unload(self):
        # USB版本硬件
        if (self.usbopen):
            self.dll.close_hiddev()

    def sendCMD(self, cmd):
        self.dll.hid007_cmd(cmd)

    def buildCMD(self, action, value1 = None, value2 = None):
        str_cmd = action
        if (value1):
            str_cmd += "," + value1
        if (value2):
            str_cmd += "," + value2
        b_cmd = str_cmd.encode('utf-8')
        return ctypes.c_char_p(b_cmd)

    # 点击按键
    def key_press(self, key):
        cmd = self.buildCMD(CMD_KEYBOARD_PRESS, key)
        self.sendCMD(cmd)

    # 按下按键
    def key_down(self, key):
        cmd = self.buildCMD(CMD_KEYBOARD_DOWN, key)
        self.sendCMD(cmd)
        # print(f"key_down: {key}")
        
    # 松开按键
    def key_up(self, key):
        cmd = self.buildCMD(CMD_KEYBOARD_UP, key)
        self.sendCMD(cmd)
        # print(f"key_up: {key}")

    # 发送HID键盘码, 使用hex16进制字符串表示，全0表示释放所有按键
    def key_hid(self, key):
        cmd = self.buildCMD(CMD_KEYBOARD_HID, key)
        self.sendCMD(cmd)

    # 发送字符串
    def key_string(self, key):
        cmd = self.buildCMD(CMD_KEYBOARD_STRING, key)
        self.sendCMD(cmd)
        
    # 释放所有按键
    def key_release(self):
        # cmd = self.buildCMD(CMD_KEYBOARD_RELEASE)
        # self.sendCMD(cmd)
        self.key_up('')

    def mouse_left_click(self):
        cmd = self.buildCMD(CMD_MOUSE_LEFT_CLICK)
        self.sendCMD(cmd)
 
    def mouse_left_down(self):
        cmd = self.buildCMD(CMD_MOUSE_LEFT_DOWN)
        self.sendCMD(cmd)
        
    def mouse_left_up(self):
        cmd = self.buildCMD(CMD_MOUSE_LEFT_UP)
        self.sendCMD(cmd)
    
    def mouse_right_click(self):
        cmd = self.buildCMD(CMD_MOUSE_RIGHT_CLICK)
        self.sendCMD(cmd)
        
    def mouse_right_down(self):
        cmd = self.buildCMD(CMD_MOUSE_RIGHT_DOWN)
        self.sendCMD(cmd)
        
    def mouse_right_up(self):
        cmd = self.buildCMD(CMD_MOUSE_RIGHT_UP)
        self.sendCMD(cmd)
        
    def mouse_relative_move(self, x, y):
        cmd = self.buildCMD(CMD_MOUSE_MOVE, str(x), str(y))
        self.sendCMD(cmd)
        
    def mouse_abs_move(self, x, y):
        cmd = self.buildCMD(CMD_MOUSE_ABS_MOVE, str(x), str(y))
        self.sendCMD(cmd)
        
    def consumer_sleep(self):
        cmd = self.buildCMD(CMD_CONSUMER_SLEEP)
        self.sendCMD(cmd)