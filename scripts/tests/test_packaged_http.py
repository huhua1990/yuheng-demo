"""Run against a locally started packaged server using YUHENG_TEST_URL."""
import os
import json
import re
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen


BASE = os.environ.get("YUHENG_TEST_URL")


@unittest.skipUnless(BASE, "set YUHENG_TEST_URL to test the packaged server")
class PackagedHttpTest(unittest.TestCase):
    def get(self, path):
        try:
            return urlopen(BASE + path, timeout=5)
        except HTTPError as response:
            return response

    def test_anonymous_root_and_client_route_return_html(self):
        for path in ("/", "/login", "/system/user"):
            with self.subTest(path=path), self.get(path) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("text/html", response.headers.get("Content-Type", ""))
                self.assertIn(b'<div id="app">', response.read())

    def test_missing_static_asset_is_404(self):
        with self.get("/assets/nonexistent-test-file.js") as response:
            self.assertEqual(response.status, 404)

    def test_bundled_javascript_is_accessible(self):
        with self.get("/") as response:
            html = response.read().decode()
        asset = re.search(r'src="(/assets/[^" ]+\.js)"', html)
        self.assertIsNotNone(asset)
        with self.get(asset.group(1)) as response:
            self.assertEqual(response.status, 200)
            self.assertTrue(response.read())

    def test_unknown_api_never_returns_html(self):
        for path in ("/admin-api/nonexistent-test", "/app-api/nonexistent-test"):
            with self.subTest(path=path), self.get(path) as response:
                self.assertNotIn("text/html", response.headers.get("Content-Type", ""))

    def test_existing_api_remains_protected(self):
        with self.get("/admin-api/system/user/page?pageNo=1&pageSize=10") as response:
            self.assertEqual(json.load(response)["code"], 401)

    @unittest.skipUnless(os.environ.get("YUHENG_TEST_CUSTOM_CONTROLLER"), "requires isolated custom controller fixture")
    def test_custom_get_controller_remains_protected(self):
        with self.get("/custom-protected-check") as response:
            body = response.read()
            self.assertNotEqual(body, b"protected fixture")
            self.assertEqual(json.loads(body)["code"], 401)


if __name__ == "__main__":
    unittest.main()
