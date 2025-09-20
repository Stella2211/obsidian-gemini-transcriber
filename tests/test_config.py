"""Tests for configuration management"""

import unittest
import os
from pathlib import Path
from unittest.mock import patch
from argparse import Namespace

from src.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class"""

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
    def test_from_env(self):
        """Test Config.from_env method"""
        config = Config.from_env()
        self.assertEqual(config.api_key, "test_api_key")
        self.assertIsNone(config.watch_folder)
        self.assertIsNone(config.db_path)
        self.assertTrue(config.create_summary)
        self.assertFalse(config.verbose)

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_no_api_key(self):
        """Test Config.from_env without API key"""
        with self.assertRaises(ValueError) as context:
            Config.from_env()
        self.assertIn("API key not found", str(context.exception))

    @patch.dict(os.environ, {"GEMINI_API_KEY": "env_api_key"})
    def test_from_args_with_env(self):
        """Test Config.from_args with environment variable"""
        args = Namespace(
            api_key=None,
            watch_folder="/test/vault",
            db_path=None,
            verbose=True,
            no_summary=False,
            scan_existing=True,
            env_file=".env",
        )
        config = Config.from_args(args)
        self.assertEqual(config.api_key, "env_api_key")
        self.assertEqual(config.watch_folder, Path("/test/vault"))
        self.assertTrue(config.verbose)
        self.assertTrue(config.create_summary)
        self.assertTrue(config.scan_existing)

    def test_from_args_with_api_key(self):
        """Test Config.from_args with explicit API key"""
        args = Namespace(
            api_key="explicit_api_key",
            watch_folder="/test/vault",
            db_path="/test/db.json",
            verbose=False,
            no_summary=True,
            scan_existing=False,
            env_file=None,
        )
        config = Config.from_args(args)
        self.assertEqual(config.api_key, "explicit_api_key")
        self.assertEqual(config.db_path, Path("/test/db.json"))
        self.assertFalse(config.create_summary)
        self.assertFalse(config.scan_existing)

    def test_get_db_path_explicit(self):
        """Test get_db_path with explicit path"""
        config = Config(api_key="test", db_path=Path("/explicit/db.json"))
        self.assertEqual(config.get_db_path(), Path("/explicit/db.json"))

    @patch("src.config.Path.exists")
    def test_get_db_path_obsidian_folder(self, mock_exists):
        """Test get_db_path with .obsidian folder"""
        mock_exists.return_value = True
        config = Config(api_key="test", watch_folder=Path("/vault"))
        expected = Path("/vault/.obsidian/.transcription_db.json")
        self.assertEqual(config.get_db_path(), expected)

    @patch("src.config.Path.exists")
    def test_get_db_path_no_obsidian_folder(self, mock_exists):
        """Test get_db_path without .obsidian folder"""
        mock_exists.return_value = False
        config = Config(api_key="test", watch_folder=Path("/vault"))
        expected = Path("/vault/.transcription_db.json")
        self.assertEqual(config.get_db_path(), expected)

    def test_get_db_path_default(self):
        """Test get_db_path with no watch folder"""
        config = Config(api_key="test")
        self.assertEqual(config.get_db_path(), Path(".transcription_db.json"))


if __name__ == "__main__":
    unittest.main()
