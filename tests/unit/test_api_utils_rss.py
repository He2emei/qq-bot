import unittest
from unittest.mock import Mock, patch

from utils.api_utils import send_group_message


class ApiUtilsRssTest(unittest.TestCase):
    @patch("utils.api_utils._napcat_ws_request", return_value=None)
    @patch("utils.api_utils.requests.get")
    def test_http_success_returns_non_empty_result(self, request_get, _ws):
        response = Mock(status_code=200, text="ok")
        response.json.side_effect = ValueError()
        request_get.return_value = response

        self.assertEqual(send_group_message(11, "hello"), {"raw": "ok"})


if __name__ == "__main__":
    unittest.main()
