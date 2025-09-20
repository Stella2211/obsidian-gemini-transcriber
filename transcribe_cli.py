#!/usr/bin/env python3
"""Command-line interface for audio transcription"""

import argparse
import sys
from pathlib import Path

from src.config import Config
from src.transcription.service import TranscriptionService
from src.utils.system import ensure_ffmpeg, validate_file_path
from src.utils.logging import setup_logging, get_logger


def main():
    """Main function for CLI transcription"""
    parser = argparse.ArgumentParser(
        description='音声ファイルをGemini APIで文字起こしします'
    )

    parser.add_argument(
        'audio_file',
        type=str,
        help='文字起こしする音声ファイルのパス'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        required=True,
        help='文字起こし結果を保存するファイルのパス'
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
        '--no-vad',
        action='store_true',
        help='VADによる分割を無効化（短い音声ファイルの場合に推奨）'
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
    logger = get_logger('cli')

    try:
        # Check for non-WAV files
        audio_path = Path(args.audio_file)
        if not audio_path.suffix.lower() == '.wav':
            ensure_ffmpeg()

        # Validate audio file
        audio_path = validate_file_path(audio_path)

        # Create configuration
        config = Config.from_args(args)

        # Create transcription service
        service = TranscriptionService(
            api_key=config.api_key,
            verbose=config.verbose
        )

        logger.info(f"Transcribing: {audio_path}")
        logger.info(f"Output: {args.output}")

        if args.verbose:
            print(f"音声ファイル: {audio_path}")
            print(f"出力ファイル: {args.output}")
            print("文字起こし中...")

        # Transcribe the audio
        transcription = service.transcribe_file(
            audio_path,
            use_vad=not args.no_vad
        )

        # Save the transcription
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcription)

        if args.verbose:
            print("\n文字起こし完了！")
            print(f"結果を {output_path} に保存しました")
            print("\n--- 文字起こし内容 (最初の500文字) ---")
            print(transcription[:500] + "..." if len(transcription) > 500 else transcription)
        else:
            print(f"文字起こし完了: {output_path}")

        logger.info("Transcription completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()