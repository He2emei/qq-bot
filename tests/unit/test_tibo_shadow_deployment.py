import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TiboShadowDeploymentTest(unittest.TestCase):
    def test_timer_attempts_to_start_on_each_wall_clock_minute(self):
        timer = (
            PROJECT_ROOT / "deploy" / "tibo-radar-apify-shadow.timer"
        ).read_text(encoding="utf-8")

        self.assertIn("OnCalendar=*-*-* *:*:00", timer)
        self.assertNotIn("OnUnitInactiveSec", timer)

    def test_service_allows_actor_run_to_finish_without_overlap(self):
        service = (
            PROJECT_ROOT / "deploy" / "tibo-radar-apify-shadow.service"
        ).read_text(encoding="utf-8")

        self.assertIn("Type=oneshot", service)
        self.assertIn("TimeoutStartSec=360", service)


if __name__ == "__main__":
    unittest.main()
