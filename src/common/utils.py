import aircv as ac
import cv2
import numpy as np
from PIL import ImageChops, Image
from src.common import config

def run_if_enabled(function):
    """
    Decorator for functions that should only run if the bot is enabled.
    :param function:    The function to decorate.
    :return:            The decorated function.
    """

    def helper(*args, **kwargs):
        if config.enabled:
            return function(*args, **kwargs)
    return helper

def transformCV2PIL(image):
    TURN = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(TURN)
    return pil_image

# end def


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
    _, maxVal, _, top_left = cv2.minMaxLoc(result)
    if (maxVal > 0.95):
        w, h = template.shape[::-1]
        bottom_right = (top_left[0] + w, top_left[1] + h)
        return top_left, bottom_right
    else:
        return -1, -1


def multi_match(frame, template, threshold=0.95):
    """
    Finds all matches in FRAME that are similar to TEMPLATE by at least THRESHOLD.
    :param frame:       The image in which to search.
    :param template:    The template to match with.
    :param threshold:   The minimum percentage of TEMPLATE that each result must match.
    :return:            An array of matches that exceed THRESHOLD.
    """

    if template.shape[0] > frame.shape[0] or template.shape[1] > frame.shape[1]:
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
    return locations


def compare_images(image_one, image_two):
    pil1 = transformCV2PIL(image_one)
    pil2 = transformCV2PIL(image_two)

    try:
        diff = ImageChops.difference(pil1, pil2)

        if diff.getbbox() is None:
            # 图片间没有任何不同则直接退出
            return True
        else:
            return False

    except ValueError as e:
        return False


def image_search(template_path):
    return config.dllTool.screenSearch(template_path)
 
    # match_result = ac.find_template(image_origin, image_template, threshold, True)
    # if match_result:
    #     rect = match_result["rectangle"]
    #     cv2.rectangle(image_origin, (rect[0][0], rect[0][1]), (rect[3][0], rect[3][1]), (0, 0, 220), 2)
    #     cv2.imshow('shot', image_origin)
    #     cv2.waitKey(0)

    # return match_result

def convert_to_relative(point, frame):
    """
    Converts POINT into relative coordinates in the range [0, 1] based on FRAME.
    Normalizes the units of the vertical axis to equal those of the horizontal
    axis by using config.mm_ratio.
    :param point:   The point in absolute coordinates.
    :param frame:   The image to use as a reference.
    :return:        The given point in relative coordinates.
    """

    x = point[0] / frame.shape[1]
    y = point[1] / config.capture.minimap_ratio / frame.shape[0]
    return x, y


def print_separator():
    """Prints a 3 blank lines for visual clarity."""

    print('\n')

def print_tag(tag):
    print_separator()
    print('#' * (10 + len(tag)))
    print(f"#    {tag}    #")
    print('#' * (10 + len(tag)))

def print_state():
    """Prints whether Auto Maple is currently enabled or disabled."""
    print_tag('ENABLED ' if config.enabled else 'DISABLED')