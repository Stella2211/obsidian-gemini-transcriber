"""Configuration management for the application"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration"""

    api_key: str
    watch_folder: Optional[Path] = None
    db_path: Optional[Path] = None
    create_summary: bool = True
    verbose: bool = False
    scan_existing: bool = False
    env_file: Path = Path(".env")

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables"""
        if env_file:
            load_dotenv(env_file)

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "API key not found. Set GEMINI_API_KEY environment variable "
                "or use --api-key option"
            )

        return cls(api_key=api_key)

    @classmethod
    def from_args(cls, args) -> "Config":
        """Create configuration from command line arguments"""
        # Load environment file if specified
        if (
            hasattr(args, "env_file")
            and args.env_file
            and os.path.exists(args.env_file)
        ):
            load_dotenv(args.env_file)

        # Get API key from args or environment
        api_key = getattr(args, "api_key", None) or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "API key not found. Set GEMINI_API_KEY environment variable "
                "or use --api-key option"
            )

        config = cls(api_key=api_key)

        # Set optional attributes
        if hasattr(args, "watch_folder"):
            config.watch_folder = Path(args.watch_folder)
        if hasattr(args, "db_path") and args.db_path:
            config.db_path = Path(args.db_path)
        if hasattr(args, "verbose"):
            config.verbose = args.verbose
        if hasattr(args, "no_summary"):
            config.create_summary = not args.no_summary
        if hasattr(args, "scan_existing"):
            config.scan_existing = args.scan_existing

        return config

    def get_db_path(self) -> Path:
        """Get the database path, using default if not specified"""
        if self.db_path:
            return self.db_path

        if self.watch_folder:
            obsidian_folder = self.watch_folder / ".obsidian"
            if obsidian_folder.exists():
                return obsidian_folder / ".transcription_db.json"
            return self.watch_folder / ".transcription_db.json"

        return Path(".transcription_db.json")
