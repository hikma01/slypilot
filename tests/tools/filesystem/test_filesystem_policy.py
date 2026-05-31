from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from slypilot.tools.filesystem import check_path_policy


class FilesystemPolicyTests(TestCase):
    def test_allows_nextcloud_and_desktop(self) -> None:
        self.assertTrue(check_path_policy("/Users/hakimradi/Nextcloud/SlyProjet", Path.cwd()).allowed)
        self.assertTrue(check_path_policy("/Users/hakimradi/Desktop", Path.cwd()).allowed)

    def test_blocks_sensitive_locations(self) -> None:
        self.assertFalse(check_path_policy("~/.ssh", Path.cwd()).allowed)
        self.assertFalse(check_path_policy("/System", Path.cwd()).allowed)
        self.assertFalse(check_path_policy("/tmp/.env", Path.cwd()).allowed)
        self.assertFalse(check_path_policy("/tmp/id_rsa", Path.cwd()).allowed)


if __name__ == "__main__":
    import unittest

    unittest.main()
