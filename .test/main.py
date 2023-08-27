import cv2
import numexpr
import numpy as np
import time
from dll_helper import dll_helper

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
    # cv2.imshow("result", src_copy)
    # cv2.waitKey()
    return results

def filter_color(img, ranges):
    """
    Returns a filtered copy of IMG that only contains pixels within the given RANGES.
    on the HSV scale.
    :param img:     The image to filter.
    :param ranges:  A list of tuples, each of which is a pair upper and lower HSV bounds.
    :return:        A filtered copy of IMG.
    """
    if img is None or len(img) == 0:
        return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, ranges[0][0], ranges[0][1])
    for i in range(1, len(ranges)):
        mask = cv2.bitwise_or(mask, cv2.inRange(
            hsv, ranges[i][0], ranges[i][1]))

    # Mask the image
    color_mask = mask > 0
    result = np.zeros_like(img, np.uint8)
    result[color_mask] = img[color_mask]
    return result

if __name__ == "__main__":
    # frame = cv2.imread(".test/Maple_A_230716_155822.png")
    # template = cv2.imread("assets/minimap_me.png")
    # # result = image_search(frame, template)
    # # result = multi_match(frame, template)
    # mm_tl = dll_helper.loadImage('assets/minimap_tl.bmp')
    # mm_br = dll_helper.loadImage('assets/minimap_br.bmp')
    # frame = dll_helper.loadImage(".test/Maple_A_230716_155822.png")
    # start = time.time()
    # tl_x, tl_y = dll_helper.screenSearch(mm_tl, 0, 0, 1000, 800)
    # end = time.time()
    # print(f'cast time: {end - start}')
    # print(tl_x, tl_y)
    # if tl_x > 0 and tl_y > 0:
    #     br_x, br_y = dll_helper.screenSearch(mm_br, tl_x + 20, tl_y + 20, tl_x + 300, tl_y+200)
    #     print(f'cast time: {time.time() - end}')
    #     print(br_x, br_y)
    
    import cv2
    import numpy as np
    import pytesseract as tess

    RUNE_LIBERATED_TEXT_RANGES = (
        ((50, 200, 46), (77, 255, 255)),
    )
    RUNE_FAILED_TEXT_RANGES = (
        ((0, 43, 46), (10, 255, 255)),
        ((156, 43, 46), (180, 255, 255)),
    )
    image = cv2.imread('.test/Maple_A_230805_034045.png')
    image = image[50:400,50:-50]
    image = filter_color(image, RUNE_LIBERATED_TEXT_RANGES)
    # cv2.imshow("", image)
    # cv2.waitKey()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    start = time.time()
    text = tess.image_to_string(image_rgb, lang="eng")
    print(time.time() - start)
    content = text.replace("\f", "").split("\n")
    for c in content:
        if len(c) > 0 and 'rune' in c.lower():
            print(c)
            list = c.split(":")
            print(list[0])
    # h, w, c = image.shape
    # boxes = tess.image_to_boxes(image)
    # for b in boxes.splitlines():
    #     b = b.split(' ')
    #     image = cv2.rectangle(image, (int(b[1]), h - int(b[2])), (int(b[3]), h - int(b[4])), (0, 255, 0), 2)

    # cv2.imshow('text detect', image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
