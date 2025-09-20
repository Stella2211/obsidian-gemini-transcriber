"""Gemini API client wrapper"""

from typing import Optional, Any
from pathlib import Path
from google import genai
from google.genai.types import File

from src.constants import TRANSCRIPTION_MODEL, SUMMARY_MODEL
from src.api.retry import retry_with_backoff
from src.utils.logging import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Wrapper for Gemini API client with retry logic"""

    def __init__(self, api_key: str):
        """
        Initialize Gemini client

        Args:
            api_key: Google API key
        """
        self.api_key = api_key
        self.transcription_model = TRANSCRIPTION_MODEL
        self.summary_model = SUMMARY_MODEL
        self.client = genai.Client(api_key=api_key)
        logger.info("Initialized Gemini client")
        logger.info(f"Transcription model: {self.transcription_model}")
        logger.info(f"Summary model: {self.summary_model}")

    def upload_file(self, file_path: Path) -> File:
        """
        Upload a file to Gemini API

        Args:
            file_path: Path to the file to upload

        Returns:
            Uploaded file object
        """
        logger.debug(f"Uploading file: {file_path}")

        def upload():
            return self.client.files.upload(file=str(file_path))

        return retry_with_backoff(upload)

    def generate_content(
        self,
        prompt: str,
        file: Optional[File] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate content using Gemini API

        Args:
            prompt: Text prompt
            file: Optional file object to include
            model: Optional model override
            **kwargs: Additional arguments for generate_content

        Returns:
            Generated text content
        """
        logger.debug(f"Generating content with prompt length: {len(prompt)}")

        # Use provided model or default to summary model
        use_model = model or self.summary_model

        def generate():
            contents = [prompt]
            if file:
                contents.append(file)

            response = self.client.models.generate_content(
                model=use_model, contents=contents, **kwargs
            )
            # Check if response has text attribute and it's not None
            if hasattr(response, "text") and response.text:
                return response.text
            else:
                # Treat None response as retryable error
                logger.warning("API response has no text content, will retry")
                from src.api.retry import RetryableError

                raise RetryableError("API returned empty response")

        return retry_with_backoff(generate)

    def transcribe_audio(
        self, audio_path: Path, segment_info: Optional[tuple[float, float]] = None
    ) -> str:
        """
        Transcribe an audio file

        Args:
            audio_path: Path to the audio file
            segment_info: Optional tuple of (start_time, end_time) for segments

        Returns:
            Transcribed text
        """
        logger.info(f"Transcribing audio: {audio_path}")

        # Upload the audio file
        audio_file = self.upload_file(audio_path)

        # Create the prompt
        if segment_info:
            start, end = segment_info
            prompt = (
                f"この音声ファイル（元の音声の{start:.1f}秒から{end:.1f}秒の部分）を"
                f"文字起こししてください。「あー」や「えーと」などの口語的な表現は削除し、内容を保ちつつ読みやすい文章にしてください。"
            )
        else:
            prompt = "この音声ファイルを文字起こししてください。「あー」や「えーと」などの口語的な表現は削除し、内容を保ちつつ読みやすい文章にしてください。"

        # Generate transcription using transcription model
        transcription = self.generate_content(
            prompt, audio_file, model=self.transcription_model
        )

        # Note: None check is now handled in generate_content with retry
        logger.info(f"Transcription completed, length: {len(transcription)} characters")

        return transcription

    def summarize_text(self, text: str, context: str = "") -> str:
        """
        Summarize text using Gemini API

        Args:
            text: Text to summarize
            context: Optional context for the summary

        Returns:
            Summary text
        """
        logger.info(f"Generating summary for text of length: {len(text)}")

        prompt = f"""以下の音声文字起こしを読んで、構造化された要約を作成してください。

要約の形式：
1. **主要なトピック**: 箇条書き
2. **重要なポイント**: 最も重要な情報を箇条書き
3. **結論・まとめ**: 完結かつ要点を押さえた文章
4. **キーワード**: 重要な用語やコンセプトとそれぞれの説明を箇条書きで

{f"コンテキスト: {context}" if context else ""}

文字起こし内容：
---
{text}
---

要約は明確で読みやすく、マークダウン形式で作成してください。"""

        # Use summary model (already default in generate_content)
        summary = self.generate_content(prompt, model=self.summary_model)

        # Note: None check is now handled in generate_content with retry
        logger.info("Summary generated successfully")

        return summary
