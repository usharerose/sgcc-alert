"""
Service for detect the notch in slide captcha
"""
import base64
import io
from typing import Tuple

import cv2
import numpy as np
from PIL import Image


CANNY_LOWER_THRESHOLD = 50
CANNY_UPPER_THRESHOLD = 100
CV_BINARY_THRESH = 45.0
CV_BINARY_MAXVAL = 255.0
CV_KERNAL_SIZE = 4


class NotchService:

    def __init__(self, bg_data_url: str, slide_data_url: str):
        self._bg_data_url = bg_data_url
        self._bg_bytes = self._decode_img_data_url(bg_data_url)
        self._slide_data_url = slide_data_url
        self._slide_bytes = self._decode_img_data_url(slide_data_url)

    @property
    def bg_data_url(self) -> str:
        return self._bg_data_url

    @property
    def bg_bytes(self) -> bytes:
        return self._bg_bytes

    @property
    def bg_data_url(self) -> str:
        return self.slide_data_url

    @property
    def slide_bytes(self) -> bytes:
        return self._slide_bytes

    def recognize_notch(self) -> Tuple[int, int]:
        """
        recognize the notch for slide block in background image
        return the coordinate point of notch's left top
        """
        bg_cv_np = self._preprocess_background()
        bg_cv_cannied_np = cv2.Canny(
            bg_cv_np,
            CANNY_LOWER_THRESHOLD,
            CANNY_UPPER_THRESHOLD
        )
        contours, _ = cv2.findContours(
            bg_cv_cannied_np,
            cv2.RETR_CCOMP,
            cv2.CHAIN_APPROX_SIMPLE
        )

        slide_width, slide_height = self.parse_slide_size()
        dx, dy = 0, 0
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            if (abs(w - slide_width) / slide_width <= 0.05) and (abs(h - slide_height) / slide_height <= 0.05):
                dx = x
                dy = y

        return dx, dy

    def parse_slide_size(self) -> Tuple[int, int]:
        """
        slide image is PNG with transparent background
        and colorful block
        return the width and height of it
        """
        im = Image.open(io.BytesIO(self._slide_bytes))
        im = im.convert('RGBA')
        min_x, min_y, max_x, max_y = im.width, im.height, 0, 0

        data = im.getdata()
        for y in range(im.height):
            for x in range(im.width):
                pixel = data[y * im.width + x]
                _, _, _, rgba_alpha = pixel
                if rgba_alpha <= 0:
                    continue
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        return width, height

    @staticmethod
    def _decode_img_data_url(data_url: str) -> bytes:
        _, b64_encoded = data_url.split(',')
        return base64.b64decode(b64_encoded)

    def _preprocess_background(self) -> np.ndarray:
        """
        convert raw captcha background image to binary image
        perform morphological opening to remove noise

        this is is the pre process for recognizing the notch
        """
        bg_np = np.frombuffer(self._bg_bytes, dtype='uint8')
        bg_cv_np = cv2.imdecode(bg_np, cv2.IMREAD_COLOR)

        bg_cv_gray_np = cv2.cvtColor(bg_cv_np, cv2.COLOR_BGR2GRAY)
        _, bg_cv_binary_np = cv2.threshold(
            bg_cv_gray_np,
            CV_BINARY_THRESH,
            CV_BINARY_MAXVAL,
            cv2.THRESH_BINARY_INV
        )
        kernel = np.ones((CV_KERNAL_SIZE, CV_KERNAL_SIZE), np.uint8)
        bg_cv_cleaned_binary_np = cv2.morphologyEx(bg_cv_binary_np, cv2.MORPH_OPEN, kernel)
        return bg_cv_cleaned_binary_np
