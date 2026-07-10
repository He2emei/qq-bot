import os
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigEnvironmentTest(unittest.TestCase):
    def test_openai_base_url_uses_environment_override(self):
        environment = os.environ.copy()
        environment["OPENAI_BASE_URL"] = "https://example.test/v1"

        result = subprocess.run(
            [sys.executable, "-c", "import config; print(config.OPENAI_BASE_URL)"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.stdout.strip(), "https://example.test/v1")


if __name__ == "__main__":
    unittest.main()
