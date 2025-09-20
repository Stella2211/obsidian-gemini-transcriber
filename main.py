#!/usr/bin/env python3
"""Main entry point for Obsidian audio transcription watcher"""

import argparse
import sys
from pathlib import Path

from src.config import Config
from src.obsidian.handler import ObsidianTranscriptionHandler
from src.obsidian.watcher import VaultWatcher
from src.utils.system import ensure_ffmpeg, validate_directory_path
from src.utils.logging import setup_logging, get_logger


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Obsidianフォルダを監視して音声ファイルを自動文字起こし'
    )

    parser.add_argument(
        'watch_folder',
        type=str,
        help='監視するObsidianフォルダのパス'
    )

    parser.add_argument(
        '-k', '--api-key',
        type=str,
        help='Google Gemini API キー（.envファイルまたは環境変数 GEMINI_API_KEY からも読み込み可能）'
    )

    parser.add_argument(
        '--env-file',
        type=str,
        default='.env',
        help='.envファイルのパス（デフォルト: .env）'
    )

    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='処理済みファイルのデータベースパス（デフォルト: vault直下の.obsidian/.transcription_db.json）'
    )

    parser.add_argument(
        '--scan-existing',
        action='store_true',
        help='起動時に既存ファイルもスキャンして処理'
    )

    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='要約の生成を無効化（文字起こしのみ）'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='詳細な出力を表示'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        help='ログファイルのパス'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='ログレベル'
    )

    args = parser.parse_args()

    # Setup logging
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(
        level=args.log_level if not args.verbose else 'DEBUG',
        log_file=log_file
    )
    logger = get_logger('main')

    try:
        # Ensure FFmpeg is installed
        ensure_ffmpeg()

        # Create configuration
        config = Config.from_args(args)

        # Validate watch folder
        vault_path = validate_directory_path(Path(args.watch_folder))
        config.watch_folder = vault_path

        # Get database path
        db_path = config.get_db_path()

        logger.info("Starting Obsidian audio transcription watcher")
        logger.info(f"Vault: {vault_path}")
        logger.info(f"Database: {db_path}")

        # Create handler
        handler = ObsidianTranscriptionHandler(
            api_key=config.api_key,
            vault_path=vault_path,
            db_path=db_path,
            create_summary=config.create_summary,
            verbose=config.verbose
        )

        # Create watcher
        watcher = VaultWatcher(
            vault_path=vault_path,
            process_callback=handler.process_audio_file
        )

        # Scan existing files if requested
        if config.scan_existing:
            logger.info("Scanning existing files")
            watcher.scan_existing_files()

        # Start watching
        logger.info("Starting file system watcher")
        print(f"\n🎧 音声ファイル監視中: {vault_path}")
        print(f"  要約生成: {'有効' if config.create_summary else '無効'}")
        print("  終了するには Ctrl+C を押してください\n")

        watcher.run_forever()

        print("\n👋 監視を終了しました")

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        print("\n👋 監視を終了しました")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()