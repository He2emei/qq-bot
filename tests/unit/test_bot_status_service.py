import unittest
from unittest.mock import Mock

from services.bot_status_service import handle_status_command


class BotStatusServiceTest(unittest.TestCase):
    def test_authorized_private_status_uses_private_sender(self):
        private_sender = Mock(return_value={"status": "ok"})
        group_sender = Mock()
        handled = handle_status_command(
            {"message_type": "private", "user_id": 42},
            "#status",
            authorized_user_id=42,
            group_sender=group_sender,
            private_sender=private_sender,
            status_builder=lambda: "healthy",
            source_ip="127.0.0.1",
            allowed_source_ips={"127.0.0.1"},
        )

        self.assertTrue(handled)
        private_sender.assert_called_once_with(42, "healthy")
        group_sender.assert_not_called()

    def test_unauthorized_status_is_consumed_without_reply(self):
        private_sender = Mock()
        group_sender = Mock()

        handled = handle_status_command(
            {"message_type": "group", "group_id": 11, "user_id": 99},
            "#status",
            authorized_user_id=42,
            group_sender=group_sender,
            private_sender=private_sender,
            status_builder=lambda: "healthy",
            source_ip="127.0.0.1",
            allowed_source_ips={"127.0.0.1"},
        )

        self.assertTrue(handled)
        private_sender.assert_not_called()
        group_sender.assert_not_called()

    def test_authorized_group_status_is_sent_privately_not_leaked_to_group(self):
        private_sender = Mock()
        group_sender = Mock()

        handled = handle_status_command(
            {"message_type": "group", "group_id": 11, "user_id": 42},
            "#status",
            authorized_user_id=42,
            group_sender=group_sender,
            private_sender=private_sender,
            status_builder=lambda: "healthy",
            source_ip="127.0.0.1",
            allowed_source_ips={"127.0.0.1"},
        )

        self.assertTrue(handled)
        private_sender.assert_called_once_with(42, "healthy")
        group_sender.assert_not_called()

    def test_status_from_untrusted_source_is_consumed_without_probe_or_reply(self):
        private_sender = Mock()
        status_builder = Mock(return_value="healthy")

        handled = handle_status_command(
            {"message_type": "private", "user_id": 42},
            "#status",
            authorized_user_id=42,
            group_sender=Mock(),
            private_sender=private_sender,
            status_builder=status_builder,
            source_ip="203.0.113.10",
            allowed_source_ips={"127.0.0.1"},
        )

        self.assertTrue(handled)
        status_builder.assert_not_called()
        private_sender.assert_not_called()


if __name__ == "__main__":
    unittest.main()
