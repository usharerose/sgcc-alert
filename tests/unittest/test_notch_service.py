"""
Unit test for NotchService
"""
from http import HTTPStatus
import json
from unittest import TestCase
from unittest.mock import patch

from sgcc_alert.notch_service import NotchService


with open('tests/mock_data/captcha_chartreux.json', 'r') as f:
    CAPTCHA_CHARTREUX_PAIR_DATA = json.load(f)
CAPTCHA_CHARTREUX_BG_DATA_URL = CAPTCHA_CHARTREUX_PAIR_DATA['background_data_url']
CAPTCHA_CHARTREUX_SLIDE_DATA_URL = CAPTCHA_CHARTREUX_PAIR_DATA['slide_data_url']
with open('tests/mock_data/captcha_cherry_donut.json', 'r') as f:
    CAPTCHA_CHERRY_DONUT_PAIR_DATA = json.load(f)
CAPTCHA_CHERRY_DONUT_BG_DATA_URL = CAPTCHA_CHERRY_DONUT_PAIR_DATA['background_data_url']
CAPTCHA_CHERRY_DONUT_SLIDE_DATA_URL = CAPTCHA_CHERRY_DONUT_PAIR_DATA['slide_data_url']
with open('tests/mock_data/captcha_notes.json', 'r') as f:
    CAPTCHA_NOTES_PAIR_DATA = json.load(f)
CAPTCHA_NOTES_BG_DATA_URL = CAPTCHA_NOTES_PAIR_DATA['background_data_url']
CAPTCHA_NOTES_SLIDE_DATA_URL = CAPTCHA_NOTES_PAIR_DATA['slide_data_url']


SLIDE_WIDTH = 68
SLIDE_HEIGHT = 50
MARGIN_ERR = 5


class NotchServiceTestCase(TestCase):

    def test_parse_slide_size(self):
        service = NotchService(
            CAPTCHA_CHARTREUX_BG_DATA_URL,
            CAPTCHA_CHARTREUX_SLIDE_DATA_URL
        )
        slide_actual_width, slide_actual_height = (
            service.parse_slide_size()
        )

        self.assertEqual(slide_actual_width, SLIDE_WIDTH)
        self.assertEqual(slide_actual_height, SLIDE_HEIGHT)

    def test_recognize_notch_with_cherry_donut(self):
        service = NotchService(
            CAPTCHA_CHERRY_DONUT_BG_DATA_URL,
            CAPTCHA_CHERRY_DONUT_SLIDE_DATA_URL
        )
        actual_x, _ = service.locate_notch()
        self.assertIn(actual_x, range(270 - MARGIN_ERR, 270 + MARGIN_ERR + 1))

    def test_recognize_notch_with_chartreux(self):
        service = NotchService(
            CAPTCHA_CHARTREUX_BG_DATA_URL,
            CAPTCHA_CHARTREUX_SLIDE_DATA_URL
        )
        actual_x, _ = service.locate_notch()
        self.assertIn(actual_x, range(153 - MARGIN_ERR, 153 + MARGIN_ERR + 1))

    def test_recognize_notch_with_notes(self):
        service = NotchService(
            CAPTCHA_NOTES_BG_DATA_URL,
            CAPTCHA_NOTES_SLIDE_DATA_URL
        )
        actual_x, _ = service.locate_notch()
        self.assertIn(actual_x, range(199 - MARGIN_ERR, 199 + MARGIN_ERR + 1))
