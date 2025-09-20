"""Voice Activity Detection (VAD) for audio splitting"""

import os
import tempfile
from pathlib import Path
from typing import List, Tuple
from pydub import AudioSegment
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

from src.constants import (
    VAD_THRESHOLD,
    VAD_SAMPLING_RATE,
    MIN_SILENCE_DURATION_MS,
    SPEECH_PAD_MS,
    MAX_SEGMENT_DURATION,
)
from src.audio.utils import get_audio_duration
from src.utils.logging import get_logger

logger = get_logger(__name__)


class VADProcessor:
    """Voice Activity Detection processor for audio splitting"""

    def __init__(self):
        """Initialize VAD processor"""
        logger.info("Initializing VAD processor")
        self.model = None

    def _ensure_model(self):
        """Ensure VAD model is loaded"""
        if self.model is None:
            logger.info("Loading Silero VAD model")
            self.model = load_silero_vad()

    def split_audio(
        self, audio_path: Path, max_duration: float = MAX_SEGMENT_DURATION
    ) -> List[Tuple[float, float, Path]]:
        """
        Split audio file using VAD

        Args:
            audio_path: Path to the audio file
            max_duration: Maximum duration for each segment in seconds

        Returns:
            List of tuples (start_time, end_time, segment_path)
        """
        logger.info(f"Splitting audio file: {audio_path}")
        self._ensure_model()

        # Convert to WAV if needed
        temp_wav_path = None
        if not str(audio_path).lower().endswith(".wav"):
            logger.debug("Converting audio to WAV format for VAD processing")
            audio = AudioSegment.from_file(str(audio_path))
            temp_wav_path = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ).name
            audio.export(temp_wav_path, format="wav")
            wav_path = temp_wav_path
        else:
            wav_path = str(audio_path)

        try:
            # Read audio and detect speech segments
            logger.debug("Reading audio file for VAD processing")
            wav = read_audio(wav_path, sampling_rate=VAD_SAMPLING_RATE)

            logger.debug("Detecting speech segments")
            speech_timestamps = get_speech_timestamps(
                wav,
                self.model,
                threshold=VAD_THRESHOLD,
                sampling_rate=VAD_SAMPLING_RATE,
                min_silence_duration_ms=MIN_SILENCE_DURATION_MS,
                speech_pad_ms=SPEECH_PAD_MS,
                return_seconds=True,
            )

            if not speech_timestamps:
                logger.warning("No speech segments detected, returning entire audio")
                return [(0, get_audio_duration(audio_path), audio_path)]

            # Group timestamps into segments based on max_duration
            segments = self._group_segments(speech_timestamps, max_duration)

            # Create audio segments
            return self._create_audio_segments(audio_path, segments)

        finally:
            # Clean up temporary WAV file
            if temp_wav_path and os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
                logger.debug("Cleaned up temporary WAV file")

    def _group_segments(
        self, timestamps: List[dict], max_duration: float
    ) -> List[Tuple[float, float]]:
        """
        Group speech timestamps into segments based on maximum duration

        Args:
            timestamps: List of speech timestamp dictionaries
            max_duration: Maximum duration for each segment

        Returns:
            List of tuples (start_time, end_time)
        """
        if not timestamps:
            return []

        segments = []
        current_start = timestamps[0]["start"]
        current_end = timestamps[0]["end"]

        for timestamp in timestamps[1:]:
            # Check if adding this timestamp would exceed max duration
            if timestamp["end"] - current_start <= max_duration:
                current_end = timestamp["end"]
            else:
                # Save current segment and start a new one
                segments.append((current_start, current_end))
                current_start = timestamp["start"]
                current_end = timestamp["end"]

        # Add the last segment
        segments.append((current_start, current_end))

        logger.info(
            f"Grouped {len(timestamps)} speech segments into {len(segments)} chunks"
        )
        return segments

    def _create_audio_segments(
        self, audio_path: Path, segments: List[Tuple[float, float]]
    ) -> List[Tuple[float, float, Path]]:
        """
        Create audio segment files from timestamp segments

        Args:
            audio_path: Original audio file path
            segments: List of (start_time, end_time) tuples

        Returns:
            List of tuples (start_time, end_time, segment_path)
        """
        logger.debug(f"Creating {len(segments)} audio segment files")
        audio = AudioSegment.from_file(str(audio_path))
        temp_files = []

        for i, (start, end) in enumerate(segments):
            start_ms = int(start * 1000)
            end_ms = int(end * 1000)

            # Extract segment
            segment = audio[start_ms:end_ms]

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_segment_{i}.wav", delete=False
            )
            segment.export(temp_file.name, format="wav")
            temp_files.append((start, end, Path(temp_file.name)))

            duration = end - start
            logger.debug(
                f"Segment {i + 1}: {start:.2f}s - {end:.2f}s (duration: {duration:.2f}s)"
            )

        return temp_files
