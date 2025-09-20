"""Application constants and configuration defaults"""

from typing import Set

# Audio file extensions
AUDIO_EXTENSIONS: Set[str] = {
    ".mp3",
    ".m4a",
    ".wav",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".webm",
    ".wma",
}

# API settings
TRANSCRIPTION_MODEL = "gemini-2.5-flash-lite"  # Model for audio transcription
SUMMARY_MODEL = "gemini-2.5-flash"  # Model for text summarization
MAX_RETRIES = 5
DEFAULT_TIMEOUT = 600  # 10 minutes
RETRY_BACKOFF_BASE = 10  # Base seconds for exponential backoff
MAX_RETRY_WAIT = 120  # Maximum wait between retries

# VAD settings
VAD_THRESHOLD = 0.5
VAD_SAMPLING_RATE = 16000
MIN_SILENCE_DURATION_MS = 500
SPEECH_PAD_MS = 30
MAX_SEGMENT_DURATION = 600  # 10 minutes

# Server error keywords for retry logic
RETRYABLE_ERROR_KEYWORDS = [
    "server",
    "service",
    "unavailable",
    "503",
    "500",
    "429",
    "rate limit",
    "quota",
    "empty response",  # Added for None responses
    "no text content",  # Added for None responses
]

# File size limits
MAX_TRANSCRIPTION_PREVIEW_LENGTH = 15000  # Characters for summary generation

# Obsidian note settings
DEFAULT_TAGS = ["音声文字起こし", "自動生成"]
SUMMARY_TAGS = ["音声要約", "自動生成"]
