import cv2
import numpy as np
import time
import matplotlib.pyplot as plt
import matplotlib as mpl
from pylab import *
import pytesseract as tess

mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False

# mpl.rcParams['font.family'] = 'SimHei'


ARROW_TL_TEMPLATE = cv2.imread('assets/rune/rune_top_left.png', 0)
ARROW_BR_TEMPLATE = cv2.imread('assets/rune/rune_br_template.png', 0)
ARROW_BL_TEMPLATE = cv2.imread('assets/rune/rune_bl_template.png', 0)

ARROW_RANGES1 = (
    ((0, 160, 180), (70, 255, 255)),
)

ARROW_RANGES2 = (
    ((1, 160, 100), (77, 255, 255)),
    ((0, 100, 200), (180, 255, 255))
)

RUNE_LIBERATED_TEXT_RANGES = (
    ((50, 200, 46), (77, 255, 255)),
)
RUNE_FAILED_TEXT_RANGES = (
    ((0, 43, 46), (10, 255, 255)),
    ((156, 43, 46), (180, 255, 255)),
)

RUNE_LIBERATED_TEXT_RANGES = (
    ((50, 200, 46), (77, 255, 255)),
)
RUNE_FAILED_TEXT_RANGES = (
    ((0, 43, 46), (10, 255, 255)),
    ((156, 43, 46), (180, 255, 255)),
)
WHITE_RANGES = (
    ((0, 0, 150), (180, 30, 255)),
)

def single_match(frame, template):
    """
    Finds the best match within FRAME.
    :param frame:       The image in which to search for TEMPLATE.
    :param template:    The template to match with.
    :return:            The top-left and bottom-right positions of the best match.
    """

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if (template.ndim > 2):
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF)
    _, _, _, top_left = cv2.minMaxLoc(result)
    h, w = template.shape[::-1]
    bottom_right = (top_left[0] + w, top_left[1] + h)

    # cv2.rectangle(frame, top_left, (top_left[0]+template.shape[1],
    #                                 top_left[1]+template.shape[0]), (0, 0, 225), 2)
    return top_left, bottom_right


def multi_match(frame, template, threshold=0.95):
    """
    Finds all matches in FRAME that are similar to TEMPLATE by at least THRESHOLD.
    :param frame:       The image in which to search.
    :param template:    The template to match with.
    :param threshold:   The minimum percentage of TEMPLATE that each result must match.
    :return:            An array of matches that exceed THRESHOLD.
    """

    if template is None or frame is None:
        return []
    if template.shape[0] > frame.shape[0] or template.shape[1] > frame.shape[1]:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if (template.ndim > 2):
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    locations = list(zip(*locations[::-1]))
    return locations


def crop_arrow_area(frame):
    height, width, channels = frame.shape
    if width < 1000:
        cropped = frame[120:height//2, 100:width-100]
    else:
        cropped = frame[120:height//2, width//4:3*width//4]
    canned = canny(cropped)
    # cv2.imshow("canned", canned)
    # cv2.imwrite("rune_br_template.png", canned)
    # cv2.waitKey()
    x = 0
    y = 0
    tl_result = multi_match(canned, ARROW_TL_TEMPLATE, threshold=0.3)
    if tl_result:
        tl = tl_result[0]
        x = tl[0] + 10
        y = tl[1] + 5
    else:
        br_result = multi_match(canned, ARROW_BR_TEMPLATE, threshold=0.3)
        if br_result:
            br = br_result[0]
            x = br[0] - 358
            y = br[1] - 42
        else:
            bl_result = multi_match(canned, ARROW_BL_TEMPLATE, threshold=0.6)
            if bl_result:
                bl = bl_result[0]
                x = bl[0] + 5
                y = bl[1] - 48

    # tl, _ = single_match(canned, ARROW_TL_TEMPLATE)

    if x > 0 and y > 0:
        w = 385
        h = 75
        cropped = cropped[y:y+h, x:x+w]
    return cropped


def filter_color(img, ranges, high_v_img=None):
    """
    Returns a filtered copy of IMG that only contains pixels within the given RANGES.
    on the HSV scale.
    :param img:     The image to filter.
    :param ranges:  A list of tuples, each of which is a pair upper and lower HSV bounds.
    :return:        A filtered copy of IMG.
    """

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, ranges[0][0], ranges[0][1])
    for i in range(1, len(ranges)):
        mask = cv2.bitwise_or(mask, cv2.inRange(
            hsv, ranges[i][0], ranges[i][1]))
        
    # if high_v_img is not None:
    #     v_mask = cv2.cvtColor(high_v_img, cv2.COLOR_BGR2GRAY)
    #     mask = cv2.bitwise_or(mask, v_mask)

    # Mask the image
    color_mask = mask > 0
    result = np.zeros_like(img, np.uint8)
    result[color_mask] = img[color_mask]
    return result


def canny(image):
    """ 
    Performs Canny edge detection on IMAGE.
    :param image:   The input image as a Numpy array.
    :return:        The edges in IMAGE.
    """

    image = cv2.Canny(image, 200, 300)
    colored = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return colored


def high_V(img):
    image = filter_color(img, (
        ((0, 100, 100), (180, 255, 255)),
    ))
    # cv2.imshow("high_V", image)
    # image = np.copy(img)
    h, w, chanels = image.shape
    # fit_list = [221, 238, 255]
    low = 220
    for x in range(w):
        for y in range(h):
            color = image[y][x]
            if color[0] > low or color[1] > low or color[2] > low:
                color[0] = color[1] = color[2] = 255
            else:
                color[0] = color[1] = color[2] = 0
    return image


def pre_filter(img, type: int):
    filtered = img
    if type == 1:
        filtered = high_V(img)
    elif type == 2:
        filtered = filter_color(img, ARROW_RANGES1)
    elif type == 3:
        filtered = filter_color(img, ARROW_RANGES2)
    return filtered


def solve_all_in_one(image, filter_type, blur, arc_filter):
    begin = time.time()

    cropped = crop_arrow_area(image)
    if cropped is None:
        print("定位失败")
        return
    all_process_images = [(cropped, "裁剪")]

    filtered = pre_filter(cropped, filter_type)
    all_process_images.append((filtered, f"filter({filter_type})"))

    processed_img, process_images = process_image(filtered, blur)

    result, resolve_images = resolve_arrow(
        processed_img, arc_filter, filter_type, blur)
    end = time.time()
    print(f"solution: {result}")
    print("cast :", end - begin)

    show_multi_images(all_process_images + process_images + resolve_images)


def show_magic(image, debug=False):
    # blur: 70,40
    # arc_filter: 0.015,0.02

    cropped = crop_arrow_area(image)
    if cropped is None:
        return None

    h, w, _ = cropped.shape
    if h == 0 or w == 0:
        return None

    filter_types = [1, 2, 3]
    begin = time.time()
    for filter_type in filter_types:

        all_process_images = [(cropped, "裁剪")]

        filtered = pre_filter(cropped, filter_type)
        all_process_images.append((filtered, f"filter({filter_type})"))

        blurs = [10, 40] if filter_type != 1 else [70]
        for blur in blurs:
            processed_img, process_images = process_image(filtered, blur)

            arc_filters = [0.04, 0.02,
                           0.01] if filter_type != 1 else [0.04]
            for arc_filter in arc_filters:
                result, resolve_images = resolve_arrow(
                    processed_img, arc_filter, filter_type, blur)

                if debug:
                    print(f"solution: {result}")
                if len(result) == 4:
                    if debug:
                        end = time.time()
                        print("cast :", end - begin)
                        show_multi_images(
                            all_process_images + process_images + resolve_images)
                    return result
    return []


def process_image(filtered, blur: int = 70):
    process_images = []

    # 转成灰度图
    img_gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
    process_images.append((img_gray, "灰度图"))

    # 进行高斯滤波ret
    img_blur = cv2.GaussianBlur(img_gray, (15, 5), 1)
    process_images.append((img_blur, "高斯滤波"))

    # 二值化，使得图片更加清晰没有中间模糊的像素点
    _, binary = cv2.threshold(img_blur, blur, 255, cv2.THRESH_BINARY)
    process_images.append((binary, f"blur({blur})"))

    # 边缘检测
    img_canny = cv2.Canny(binary, 200, 300)
    process_images.append((img_canny, "canny"))

    return img_canny, process_images


def resolve_arrow(img_canny, arc_filter=0.015, filter_type=2, blur=10):
    tmp_imgs = []

    contours, _ = cv2.findContours(
        img_canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    filtered_contours = []
    for contour in contours:
        if 350 <= cv2.contourArea(contour) <= 800 and cv2.arcLength(contour, True) > 60:
            needAdd = True
            for filtered_contour in filtered_contours:
                if abs(filtered_contour[0][0][0] - contour[0][0][0]) <= 1:
                    needAdd = False
                    break
            if needAdd:
                filtered_contours.append(contour)

    temp = np.ones(img_canny.shape, np.uint8) * 0
    cv2.drawContours(temp, filtered_contours, -1, (255, 255, 255), 1)
    tmp_imgs.append((temp, f"filtered_contours({arc_filter})"))

    polygons = []
    for contour in filtered_contours:
        arclength_filter = arc_filter * cv2.arcLength(contour, True)
        polygons.append(cv2.approxPolyDP(contour, arclength_filter, True))

    temp = np.ones(img_canny.shape, np.uint8) * 0
    cv2.drawContours(temp, polygons, -1, (255, 255, 255), 1)
    tmp_imgs.append((temp, "polygons"))

    if len(polygons) == 0:
        return [], []

    result = []
    show = []
    for polygon in polygons:
        sides = []
        n_points = len(polygon)
        for i, vertex in enumerate(polygon):
            j = (i + 1) % n_points
            p1 = vertex[0]
            p2 = polygon[j][0]
            d = (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2
            sides.append((p1, p2, d))
        sides = sorted(sides, key=lambda side: side[2], reverse=True)
        p1 = sides[0][0]
        p2 = sides[0][1]
        p3 = sides[1][0]
        p4 = sides[1][1]
        if arc_filter > 0.02:
            direct = polygon_direction(polygon)
                        
            if direct:
                result.append([direct, p1[0]])
            continue
        
        distances = [[distance(p1, p3), 1],
                     [distance(p1, p4), 2],
                     [distance(p2, p3), 3],
                     [distance(p2, p3), 4]]
        tow_board = []
        distances = sorted(distances, key=lambda distance: distance[0])
        if distances[0][1] == 1:
            dire = arrow_direction(p2, p1, p4)
            tow_board = [[p2], [p1], [p4]]
        elif distances[0][1] == 2:
            dire = arrow_direction(p2, p1, p3)
            tow_board = [[p2], [p1], [p3]]
        elif distances[0][1] == 3:
            dire = arrow_direction(p1, p2, p4)
            tow_board = [[p1], [p2], [p4]]
        else:
            dire = arrow_direction(p1, p2, p3)
            tow_board = [[p1], [p2], [p3]]

        if dire is not None:
            result.append([dire, p1[0]])
        show.append(tow_board)
    result = sorted(result, key=lambda result: result[1])
    if len(result) > 0:
        result = np.array(result)[:, 0].tolist()

    temp = np.ones(img_canny.shape, np.uint8) * 0
    for item in show:
        cv2.line(temp, item[0][0], item[1][0], (255, 255, 255), 1)
        cv2.line(temp, item[1][0], item[2][0], (255, 255, 255), 1)
    # cv2.drawContours(temp, np.array(show), -1, (255, 255, 255), 1)
    tmp_imgs.append((temp, "arrows"))

    return result, tmp_imgs

def polygon_direction(polygon):
    n_points = len(polygon)
    direct = None
    for i, vertex in enumerate(polygon):
        j = (i + 1) % n_points
        p1 = vertex[0]
        p2 = polygon[j][0]
        d = (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2

        if abs(p1[0] - p2[0]) <= 1 and d >= 9:
            direct = 'left'
            p = p2 if p1[0] < p2[0] else p1
            for i, vertex in enumerate(polygon):
                if vertex[0][0] > p[0]:
                    direct = None
                    break
            if direct:
                break
            direct = 'right'
            p = p2 if p1[0] > p2[0] else p1
            for i, vertex in enumerate(polygon):
                if vertex[0][0] < p[0]:
                    direct = None
                    break
            if direct:
                break
        elif abs(p1[1] - p2[1]) <= 1 and d >= 9:
            direct = 'down'
            p = p1 if p1[1] < p2[1] else p2
            for i, vertex in enumerate(polygon):
                if vertex[0][1] < p[1]:
                    direct = None
                    break
            if direct:
                break
            direct = 'up'
            p = p2 if p1[1] < p2[1] else p1
            for i, vertex in enumerate(polygon):
                if vertex[0][1] > p[1]:
                    direct = None
                    break
            if direct:
                break
            
    
    return direct

def arrow_direction(p1, p2, p3) -> str:
    x1 = p1[0]
    x2 = p2[0]
    x3 = p3[0]
    y1 = p1[1]
    y2 = p2[1]
    y3 = p3[1]
    if y1 <= y2 <= y3 or y3 <= y2 < y1:
        # Left or right arrow
        if x2 < x1 and x2 < x3:
            return "left"
        elif x2 > x1 and x2 > x3:
            return "right"
    elif x1 <= x2 <= x3 or x3 <= x2 <= x1:
        # Up or down arrow
        if y2 < y1 and y2 < y3:
            return "up"
        elif y2 > y1 and y2 > y3:
            return "down"
    return None


def distance(p1, p2) -> int:
    return (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2


def show_multi_images(images):
    # mpl.rcParams['figure.facecolor'] = 'black'
    subplots_adjust(bottom=0, top=1, hspace=0.2)

    for i, item in enumerate(images):
        img = item[0]
        title = item[1]
        # 行，列，索引
        plt.subplot(9, 1, i+1)
        pic1 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.imshow(pic1)
        plt.title(title, fontsize=12, color="red")
        plt.axis('off')  # 不显示坐标轴

    plt.show()


def located_arrows(frame):
    height, width, _ = frame.shape
    if width < 1000:
        cropped = frame[120:height//2, 100:width-100]
    else:
        cropped = frame[120:height//2, width//4:3*width//4]
    canned = canny(cropped)
    cv2.imshow("", canned)
    cv2.waitKey(0)
    result = multi_match(canned, ARROW_TL_TEMPLATE, 0.3)
    return len(result) > 0


def rune_interact_result(frame):
    image = frame[130:200, 400:-400]
    # image_success = filter_color(image, WHITE_RANGES)
    # cv2.imshow('', image_success)
    # cv2.waitKey()
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    text = tess.image_to_string(image_rgb, lang="eng")
    content = text.replace("\f", "").lower()
    keywords = ['tap', 'arrow', 'keys', 'correct', 'order', 'activate', 'rune']
    if len(content) > 0:
        for keyword in keywords:
            if keyword in content:
                print(content)
                return True
    return False

def rune_liberate_result(frame):
    image = frame[50:400, 50:-50]
    image_success = filter_color(image, RUNE_LIBERATED_TEXT_RANGES)
    # cv2.imshow("", image)
    # cv2.waitKey()
    # hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    image_rgb = cv2.cvtColor(image_success, cv2.COLOR_BGR2RGB)
    text = tess.image_to_string(image_rgb, lang="eng")
    content = text.replace("\f", "").split("\n")
    for c in content:
        if len(c) > 0 and 'rune of' in c.lower():
            print(c)
            print('\n')
            list = c.split(":")
            return list[0]

    # image_failed = filter_color(image, RUNE_FAILED_TEXT_RANGES)
    # image_rgb = cv2.cvtColor(image_failed, cv2.COLOR_BGR2RGB)
    # text = tess.image_to_string(image_rgb, lang="eng")
    # content = text.replace("\f", "").split("\n")
    # for c in content:
    #     if len(c) > 0:
    #         print(c)
    #         return None
    return None


# def preprocess(img):
#     img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     img_blur = cv2.GaussianBlur(img_gray, (5, 5), 1)#进行高斯滤波ret,

#     # img_thr = cv2.threshold(img_blur,70,255,cv2.THRESH_BINARY)#二值化，使得图片更加清晰没有中间模糊的像素点
#     # cv2.imshow("2",img_thr)
#     img_canny = cv2.Canny(img_blur, 200, 300)#边缘检测
#     cv2.imshow("img_canny",img_canny)

#     kernel = np.ones((2, 2),np.uint8)
#     img_dilate = cv2.dilate(img_canny, kernel, iterations =2)#边缘膨胀膨胀
#     cv2.imshow("img_dilate",img_dilate)
#     img_erode = cv2.erode(img_dilate, kernel, iterations =1)#边缘腐蚀腐蚀
#     cv2.imshow("img_erode",img_erode)
    # return img_erode

# def single_canny_match(frame, template):
#     image = canny(frame)


if __name__ == '__main__':
    image = cv2.imread('screenshot/Maple_230712_154714.png')
    show_magic(image)
