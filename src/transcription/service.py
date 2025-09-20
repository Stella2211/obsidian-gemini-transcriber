"""Audio transcription service"""

import os
from pathlib import Path
from typing import Optional

from src.api.client import GeminiClient
from src.audio.vad import VADProcessor
from src.audio.utils import get_audio_duration
from src.constants import MAX_TRANSCRIPTION_PREVIEW_LENGTH
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TranscriptionService:
    """Service for transcribing audio files"""

    def __init__(self, api_key: str, verbose: bool = False):
        """
        Initialize transcription service

        Args:
            api_key: Gemini API key
            verbose: Enable verbose logging
        """
        self.client = GeminiClient(api_key)
        self.vad_processor = VADProcessor()
        self.verbose = verbose
        logger.info("Initialized transcription service")

    def transcribe_file(
        self, audio_path: Path, use_vad: bool = True, vad_threshold_seconds: float = 600
    ) -> str:
        """
        Transcribe an audio file

        Args:
            audio_path: Path to the audio file
            use_vad: Whether to use VAD for long files
            vad_threshold_seconds: Duration threshold for using VAD

        Returns:
            Transcribed text
        """
        logger.info(f"Starting transcription for: {audio_path}")

        try:
            duration = get_audio_duration(audio_path)
            logger.info(f"Audio duration: {duration:.2f} seconds")

            if use_vad and duration > vad_threshold_seconds:
                return self._transcribe_with_vad(audio_path)
            else:
                return self._transcribe_direct(audio_path)

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def _transcribe_direct(self, audio_path: Path) -> str:
        """
        Transcribe audio file directly without splitting

        Args:
            audio_path: Path to the audio file

        Returns:
            Transcribed text
        """
        logger.info("Transcribing audio directly (no splitting)")
        return self.client.transcribe_audio(audio_path)

    def _transcribe_with_vad(self, audio_path: Path) -> str:
        """
        Transcribe audio file with VAD splitting

        Args:
            audio_path: Path to the audio file

        Returns:
            Transcribed text
        """
        logger.info("Transcribing audio with VAD splitting")

        # Split audio using VAD
        segments = self.vad_processor.split_audio(audio_path)
        logger.info(f"Audio split into {len(segments)} segments")

        transcriptions = []
        for i, (start, end, segment_path) in enumerate(segments):
            logger.info(f"Processing segment {i + 1}/{len(segments)}")

            try:
                # Transcribe segment
                try:
                    segment_text = self.client.transcribe_audio(
                        segment_path, segment_info=(start, end)
                    )
                    transcriptions.append(segment_text)
                except Exception as e:
                    logger.error(f"Failed to transcribe segment {i + 1}: {e}")
                    # Continue with other segments even if one fails
                    transcriptions.append(
                        f"[セグメント {i + 1} の文字起こしに失敗: {e}]"
                    )
            finally:
                # Clean up temporary segment file
                if segment_path.exists():
                    os.remove(segment_path)
                    logger.debug(f"Cleaned up segment file: {segment_path}")

        # Combine transcriptions
        full_transcription = "\n\n".join(transcriptions)
        logger.info(
            f"Transcription completed, total length: {len(full_transcription)} characters"
        )

        return full_transcription

    def generate_summary(
        self, transcription: str, audio_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Generate a summary of the transcription

        Args:
            transcription: The transcribed text
            audio_path: Optional path to the original audio file for context

        Returns:
            Summary text or None if generation fails
        """
        try:
            logger.info("Generating summary of transcription")

            # Truncate transcription if too long
            preview = transcription[:MAX_TRANSCRIPTION_PREVIEW_LENGTH]
            if len(transcription) > MAX_TRANSCRIPTION_PREVIEW_LENGTH:
                preview += "\n\n[文字起こしの続きは省略されています...]"

            # Add context if audio path is provided
            context = ""
            if audio_path:
                context = f"音声ファイル: {audio_path.name}"

            summary = self.client.summarize_text(preview, context)
            logger.info("Summary generated successfully")
            return summary

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return None
