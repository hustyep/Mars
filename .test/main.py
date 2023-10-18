import cv2
# import cv2.typing
import typing
import threading

import numpy as np
import time
# from dll_helper import dll_helper
# from usb import usb
from rune import *

def image_equal(image, template):
    height, width, channel = image.shape
    t_height, t_width, t_channel = template.shape
    
    if height != t_height or width != t_width or channel != t_channel:
        return False
    for row in range(0, height):
        for col in range(0, width):
            image_color = image[row][col]
            template_color = template[row][col]
            if image_color[0] != template_color[0] or image_color[1] != template_color[1] or image_color[2] != template_color[2]:
                return False
    return True

def image_search(frame, template):
    height, width, channel = frame.shape
    t_height, t_width, t_channel = template.shape
    
    if height < t_height or width < t_width or channel != t_channel:
        return
    
    for row in range(0, height):
        if height - row < t_height:
            break
        for col in range(0, width):
            if width - col < t_width:
                break
            image = frame[row:row + t_height, col:col + t_width]
            if image_equal(image, template):
                return col, row
    
    return -1, -1

def multi_match(frame, template, threshold=0.95):
    """
    Finds all matches in FRAME that are similar to TEMPLATE by at least THRESHOLD.
    :param frame:       The image in which to search.
    :param template:    The template to match with.
    :param threshold:   The minimum percentage of TEMPLATE that each result must match.
    :return:            An array of matches that exceed THRESHOLD.
    """

    if frame is None or template.shape[0] > frame.shape[0] or template.shape[1] > frame.shape[1]:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if (template.ndim > 2):
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    locations = list(zip(*locations[::-1]))
    results = []
    src_copy = frame.copy()
    for p in locations:
        x = int(round(p[0] + template.shape[1] / 2))
        y = int(round(p[1] + template.shape[0] / 2))
        results.append((x, y))

        cv2.rectangle(src_copy, p, (p[0]+template.shape[1],
                      p[1]+template.shape[0]), (0, 0, 225), 2)
    if len(results) > 0:
        cv2.imshow("result", src_copy)
        cv2.waitKey()
    return results

def filter_color(img, ranges):
    """
    Returns a filtered copy of IMG that only contains pixels within the given RANGES.
    on the HSV scale.
    :param img:     The image to filter.
    :param ranges:  A list of tuples, each of which is a pair upper and lower HSV bounds.
    :return:        A filtered copy of IMG.
    """
    if img is None or img.shape[0] == 0 or img.shape[1] == 0:
        return None # type: ignore
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, ranges[0][0], ranges[0][1])
    for i in range(1, len(ranges)):
        mask = cv2.bitwise_or(mask, cv2.inRange(
            hsv, ranges[i][0], ranges[i][1]))

    # Mask the image
    color_mask = mask > 0 # type: ignore
    result = np.zeros_like(img, np.uint8)
    result[color_mask] = img[color_mask]
    return result


def rune_test():
    frame = cv2.imread(".test/maple_231003174903228.png")
    rune_interact_result(frame)


def mob_detect_test():
    frame = cv2.imread(".test/maple_231015235452192.png")
    
    # PLAYER_SLLEE_TEMPLATE = cv2.imread('assets/roles/player_sllee_template.png', 0)
    # player_match = multi_match(frame, PLAYER_SLLEE_TEMPLATE, threshold=0.9)
    # player_pos = (player_match[0][0] - 5, player_match[0][1] - 55)
    # crop = frame[player_pos[1]-200:player_pos[1]+100, player_pos[0]-300:player_pos[0]+300]
    
    MOB_TEMPLATE_L = cv2.imread('assets/mobs/Sandblade_elite.png', 0)
    MOB_TEMPLATE_R = cv2.flip(MOB_TEMPLATE_L, 1)
    # h, w = MOB_TEMPLATE_L.shape
    # MOB_TEMPLATE_ELITE = cv2.resize(MOB_TEMPLATE_L, (w * 2, h * 2))
    start = time.time()
    mobs = multi_match(frame, MOB_TEMPLATE_L, threshold=0.95)
    mobs = multi_match(frame, MOB_TEMPLATE_R, threshold=0.95)
    print(f'{time.time() - start}')
    
def white_room_test():
    frame = cv2.imread(".test/Maple_230919_051849.png")

    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # gray = gray[100:-100, 50:-50]
    # cv2.imshow('', gray)
    # cv2.waitKey()
    # height, width = gray.shape

    # # Check for white room
    # percent = np.count_nonzero(gray == 255) / height / width
    # print(percent)
    start = time.time()
    TEMPLATE = cv2.imread('assets/white_room_template.png', 0)
    result = multi_match(frame, TEMPLATE, 1)
    print(f'{time.time() - start}')
    # print(result)

if __name__ == "__main__":
    # rune_test()
    mob_detect_test()