import unittest
from unittest.mock import Mock, patch

from utils.api_utils import send_group_forward_message, send_group_message, send_private_message


class ApiUtilsRssTest(unittest.TestCase):
    @patch("utils.api_utils._napcat_ws_request", return_value=None)
    @patch("utils.api_utils.requests.get")
    def test_http_success_returns_non_empty_result(self, request_get, _ws):
        response = Mock(status_code=200, text="ok")
        response.json.side_effect = ValueError()
        request_get.return_value = response

        self.assertEqual(send_group_message(11, "hello"), {"raw": "ok"})

    @patch("utils.api_utils._napcat_ws_request", return_value=None)
    @patch("utils.api_utils.requests.get")
    def test_http_onebot_failure_is_not_reported_as_sent(self, request_get, _ws):
        response = Mock(status_code=200, text="failed")
        response.json.return_value = {"status": "failed", "retcode": 100}
        request_get.return_value = response

        self.assertIsNone(send_group_message(11, "hello"))

    @patch("utils.api_utils._napcat_ws_request", return_value=None)
    @patch("utils.api_utils.requests.post")
    def test_forward_onebot_failure_is_not_reported_as_sent(self, request_post, _ws):
        response = Mock(status_code=200, text="failed")
        response.json.return_value = {"status": "failed", "retcode": 100}
        request_post.return_value = response

        self.assertIsNone(send_group_forward_message(11, []))

    @patch("utils.api_utils._napcat_ws_request", return_value=None)
    @patch("utils.api_utils.requests.get")
    def test_private_message_uses_same_onebot_success_check(self, request_get, _ws):
        response = Mock(status_code=200, text="ok")
        response.json.return_value = {"status": "ok", "retcode": 0}
        request_get.return_value = response

        self.assertEqual(send_private_message(42, "hello"), {"status": "ok", "retcode": 0})


if __name__ == "__main__":
    unittest.main()
