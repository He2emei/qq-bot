import unittest
from unittest.mock import patch

import requests

from services.rss_service import RssFetchError, fetch_rss_entries


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        return None


class RssServiceTest(unittest.TestCase):
    def test_fetch_rss_entries_normalizes_items(self):
        rss_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Example Feed</title>
    <item>
      <title>First item</title>
      <link>https://example.com/first</link>
      <guid>first-guid</guid>
      <pubDate>Tue, 02 Jun 2026 01:44:04 +0000</pubDate>
      <description>First summary</description>
      <content:encoded><![CDATA[
        <h1>Full report</h1>
        <p>Full body with <a href="https://example.com/source">source</a>.</p>
        <p><img src="https://example.com/image.png" /></p>
      ]]></content:encoded>
    </item>
    <item>
      <title>Second item</title>
      <link>https://example.com/second</link>
      <description>Second summary</description>
    </item>
  </channel>
</rss>"""

        with patch("services.rss_service.requests.get", return_value=FakeResponse(rss_xml)):
            entries = fetch_rss_entries("https://example.com/rss.xml", limit=1)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].title, "First item")
        self.assertEqual(entries[0].link, "https://example.com/first")
        self.assertEqual(entries[0].published, "Tue, 02 Jun 2026 01:44:04 +0000")
        self.assertEqual(entries[0].summary, "First summary")
        self.assertIn("<h1>Full report</h1>", entries[0].content_html)
        self.assertIn("Full report", entries[0].content_text)
        self.assertIn("source (https://example.com/source)", entries[0].content_text)
        self.assertIn("[图片] https://example.com/image.png", entries[0].content_text)
        self.assertEqual(entries[0].entry_id, "first-guid")

    def test_fetch_rss_entries_raises_on_request_error(self):
        with patch(
            "services.rss_service.requests.get",
            side_effect=requests.Timeout("timeout"),
        ):
            with self.assertRaises(RssFetchError):
                fetch_rss_entries("https://example.com/rss.xml")


if __name__ == "__main__":
    unittest.main()
