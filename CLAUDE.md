# Obsidian Gemini Transcriber Project Documentation

## Project Overview

Google Gemini APIを使用した音声文字起こしシステム。長時間音声のVAD分割、Obsidian統合、自動要約生成機能を提供。

## Architecture

### Directory Structure

```
gemini-stt/
├── src/
│   ├── api/          # Gemini API関連
│   │   ├── client.py      # APIクライアントラッパー
│   │   └── retry.py       # リトライロジック
│   ├── audio/        # 音声処理
│   │   ├── utils.py       # 音声ユーティリティ
│   │   └── vad.py         # VAD分割処理
│   ├── transcription/# 文字起こしサービス
│   │   └── service.py     # 統合サービス
│   ├── obsidian/     # Obsidian統合
│   │   ├── watcher.py     # ファイル監視
│   │   ├── handler.py     # 処理ハンドラ
│   │   ├── note.py        # ノート生成
│   │   └── database.py    # 処理済みファイルDB
│   ├── utils/        # 共通ユーティリティ
│   │   ├── logging.py     # ロギング設定
│   │   └── system.py      # システムユーティリティ
│   ├── config.py     # 設定管理
│   └── constants.py  # 定数定義
├── tests/           # ユニットテスト
├── main.py         # メインエントリポイント（Obsidian監視）
└── transcribe_cli.py # CLIツール（単体ファイル処理）
```

## Core Components

### 1. API Client (`src/api/client.py`)

**Class: `GeminiClient`**
- Gemini APIのラッパー
- 2つのモデルを使い分け:
  - `TRANSCRIPTION_MODEL`: gemini-2.5-flash-lite（文字起こし用）
  - `SUMMARY_MODEL`: gemini-2.5-flash（要約用）
- リトライロジックと統合

**Key Methods:**
- `transcribe_audio()`: 音声ファイルの文字起こし
- `summarize_text()`: テキストの要約生成
- `upload_file()`: ファイルのアップロード
- `generate_content()`: コンテンツ生成（モデル指定可能）

### 2. Audio Processing (`src/audio/`)

**VAD Processor (`vad.py`)**
- Silero VAD v6使用
- 10分以上の音声を自動分割
- 音声区間検出で自然な分割点を決定

**Audio Utils (`utils.py`)**
- 音声ファイル判定
- 長さ・サイズ取得
- フォーマット処理

### 3. Transcription Service (`src/transcription/service.py`)

**Class: `TranscriptionService`**
- 音声処理の統合サービス
- VAD分割の自動判定（10分閾値）
- セグメント単位の処理と結合

### 4. Obsidian Integration (`src/obsidian/`)

**Components:**
- `VaultWatcher`: ファイルシステム監視
- `ObsidianTranscriptionHandler`: 処理統合
- `NoteGenerator`: Markdownノート生成
- `ProcessedFilesDatabase`: 処理済みファイルDB（v1.0.0）

**Database Schema (v1.0.0):**
```json
{
  "version": "1.0.0",
  "created_at": "ISO-8601",
  "last_updated": "ISO-8601",
  "statistics": {
    "total_processed": 0,
    "total_failed": 0,
    "total_size_bytes": 0,
    "total_duration_seconds": 0
  },
  "files": {
    "path/to/file": {
      "hash": "md5",
      "status": "completed|failed|pending",
      "processed_at": "ISO-8601",
      "updated_at": "ISO-8601",
      "outputs": {
        "transcription": "path",
        "summary": "path|null"
      },
      "metadata": {
        "duration_seconds": 0,
        "file_size_bytes": 0
      },
      "error": "string|null"
    }
  }
}
```

## Configuration

### Environment Variables

```bash
GEMINI_API_KEY=your_api_key  # Required
```

### Constants (`src/constants.py`)

```python
# Models
TRANSCRIPTION_MODEL = 'gemini-2.5-flash-lite'
SUMMARY_MODEL = 'gemini-2.5-flash'

# Audio
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.wav', ...}
MAX_SEGMENT_DURATION = 600  # 10 minutes

# Retry
MAX_RETRIES = 5
DEFAULT_TIMEOUT = 600  # 10 minutes
RETRY_BACKOFF_BASE = 10
MAX_RETRY_WAIT = 120

# VAD
VAD_THRESHOLD = 0.5
VAD_SAMPLING_RATE = 16000
MIN_SILENCE_DURATION_MS = 500
SPEECH_PAD_MS = 30
```

## Usage Patterns

### Basic Flow

1. **Audio Detection**: ファイル監視またはCLI引数
2. **Processing**:
   - ハッシュチェックで重複判定
   - VAD分割（長時間音声）
   - Gemini APIで文字起こし
   - 要約生成（オプション）
3. **Output**:
   - `_文字起こし.md`: 完全な文字起こし
   - `_要約.md`: 構造化された要約
4. **Database Update**: 処理済み記録

### Error Handling

- **Retry Logic**: 指数バックオフで最大5回
- **Timeout**: 10分でタイムアウト
- **Failed Files**: DBに記録して再処理可能
- **Logging**: 詳細なログ出力

## Dependencies

### Core
- `google-genai>=1.38.0`: Gemini API
- `python-dotenv>=1.1.1`: 環境変数
- `watchdog>=6.0.0`: ファイル監視

### Audio
- `pydub>=0.25.1`: 音声処理
- `soundfile>=0.13.1`: 音声メタデータ
- `silero-vad>=6.0`: VAD
- `torch>=2.8.0`, `torchaudio>=2.8.0`: VAD依存

### System Requirements
- Python 3.8+
- FFmpeg（非WAV形式）

## Package Management

### uv (Recommended)
```bash
uv sync          # 依存関係インストール
uv run main.py   # 実行
```

### pip
```bash
pip install -r requirements.txt
python main.py
```

## Testing

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=src

# Specific test
uv run pytest tests/test_database.py
```

## Common Tasks

### Add New Audio Format
1. `src/constants.py`の`AUDIO_EXTENSIONS`に追加
2. FFmpeg対応確認

### Change Models
1. `src/constants.py`の`TRANSCRIPTION_MODEL`/`SUMMARY_MODEL`を変更

### Customize Prompts
1. `src/api/client.py`の`transcribe_audio()`/`summarize_text()`内のプロンプト編集

### Add Processing Status
1. `src/obsidian/database.py`の`ProcessingStatus` Enumに追加

## Performance Considerations

- **VAD Split**: 10分閾値で自動分割
- **Parallel Processing**: セグメント処理は順次（API制限考慮）
- **Caching**: 処理済みファイルはハッシュで判定
- **Memory**: 長時間音声は分割処理でメモリ効率化

## Security

- APIキーは環境変数で管理
- `.env`ファイルは`.gitignore`に含める
- ログにAPIキーを含めない

## Future Improvements

- [ ] バッチ処理モード
- [ ] 並列処理オプション
- [ ] Web UI
- [ ] 他の音声認識APIサポート
- [ ] リアルタイム処理