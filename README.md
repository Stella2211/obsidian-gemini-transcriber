# Obsidian Gemini Transcriber

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![uv](https://img.shields.io/badge/uv-compatible-orange)](https://github.com/astral-sh/uv)

Google Gemini APIを使用した高速・高精度な音声文字起こしツールです。指定されたフォルダを監視し、新しい音声ファイルを検知したら自動で文字起こし・要約の生成を行います。
このプロジェクトとObsidian Syncを組み合わせることで、音声メモや会議の録音をObsidianにアップロードするだけで、自動的に文字起こしと要約が生成され、効率的な情報管理が可能になります。

## ✨ 特徴
- 🎙️ **多様な音声形式対応**: MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, WEBM, WMA
- 🔄 **自動分割処理**: 長時間音声をVAD（Voice Activity Detection）で自動分割。これにより、Gemini APIの出力トークン制限を回避しつつ、文中での途切れがない自然な文字起こしを実現。
- 📁 **フォルダ監視**: フォルダを監視して、新しい音声ファイルが検知されたら自動文字起こし・要約を生成。
- 📝 **Obsidian連携**:Obsidian Syncと組み合わせることにより、音声メモや会議の録音を自動的に文字起こし・要約することが可能。
- 🔒 **信頼性**: エラーハンドリングやリトライ機能を搭載。

## 📋 必要条件

- Python 3.8以上
- Google Gemini API キー
- FFmpeg（非WAV形式の処理に必要）

## 🚀 クイックスタート

### uvを使用（推奨・高速）

```bash
# uvのインストール（まだの場合）
pip install uv

# プロジェクトの初期化と依存関係のインストール
uv sync

# Obsidian監視モード
uv run main.py /path/to/obsidian/vault

# 単体ファイルの文字起こし
uv run transcribe_cli.py audio.mp3 -o output.txt
```

### pipを使用

```bash
# 依存関係のインストール
pip install -r requirements.txt

# Obsidian監視モード
python main.py /path/to/obsidian/vault

# 単体ファイルの文字起こし
python transcribe_cli.py audio.mp3 -o output.txt
```

## ⚙️ セットアップ

### 1. FFmpegのインストール

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

### 2. APIキーの設定

`.env`ファイルを作成：
```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## 📚 使用方法

### フォルダ監視モード

新しい音声ファイルを自動的に検出して処理：

```bash
# 基本的な使用
python main.py /path/to/obsidian/vault

# 既存ファイルもスキャン
python main.py /path/to/obsidian/vault --scan-existing

# 要約を無効化（文字起こしのみ）
python main.py /path/to/obsidian/vault --no-summary

# 詳細ログ表示
python main.py /path/to/obsidian/vault -v

# ログファイル出力
python main.py /path/to/obsidian/vault --log-file app.log
```

### CLIモード

単体ファイルの文字起こし：

```bash
# 基本的な使用
python transcribe_cli.py audio.mp3 -o output.txt

# VAD分割を無効化（短い音声向け）
python transcribe_cli.py audio.mp3 -o output.txt --no-vad

# 詳細表示
python transcribe_cli.py audio.mp3 -o output.txt -v
```

### 生成されるファイル

1. **`ファイル名_文字起こし.md`**: 完全な文字起こし内容
   - メタ情報（録音時間、ファイルサイズ等）
   - タイムスタンプ
   - 全文テキスト

2. **`ファイル名_要約.md`**: AI生成の構造化要約
   - 主要トピック（3-5個）
   - 重要ポイント（5-7個）
   - 結論・まとめ
   - キーワード

## 🏗️ プロジェクト構造

```
src/
├── api/          # Gemini APIクライアント・リトライロジック
├── audio/        # 音声処理・VAD
├── transcription/# 文字起こしサービス
├── obsidian/     # Obsidian統合
│   ├── watcher.py    # ファイル監視
│   ├── note.py       # ノート生成
│   ├── handler.py    # 処理ハンドラ
│   └── database.py   # 処理済みファイルDB
├── utils/        # ユーティリティ
└── config.py     # 設定管理
```

## 🗄️ データベース

処理済みファイルは自動的に追跡され、重複処理を防ぎます：

- **保存場所**: `.obsidian/.transcription_db.json`
- **統計情報**: 処理数、合計時間、エラー数等
- **オーファン削除**: 削除されたファイルのエントリを自動クリーンアップ

## 🛠️ 開発

### 開発環境のセットアップ

```bash
# uvを使用
uv sync --dev

# または pip
pip install -r requirements-dev.txt
```

### テストの実行

```bash
# 全テスト実行
uv run pytest

# カバレッジレポート付き
uv run pytest --cov=src --cov-report=html
```

### コード品質チェック

```bash
# フォーマット
uv run black src tests

# 型チェック
uv run mypy src

# Linting
uv run flake8 src tests
```

## 📊 技術仕様

- **最大音声長**: 制限なし（10分以上は自動分割）
- **VAD分割閾値**: 10分（600秒でセグメント化）
- **使用モデル**: Gemini 2.5 Flash Lite(文字起こし), Gemini 2.5 Flash (要約)
- **VADモデル**: Silero VAD v6
- **リトライ**: 最大5回（指数バックオフ）
- **タイムアウト**: 10分（600秒）
- **対応Python**: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

## 🐛 トラブルシューティング

### FFmpeg関連のエラー
```bash
# インストール確認
ffmpeg -version

# 権限確認（Linux/Mac）
which ffmpeg
```

### メモリ不足エラー
- 長時間音声（数時間）はVAD分割を有効化
- `--no-vad`オプションは短い音声のみ使用

### APIエラー
- APIキーの確認: `.env`ファイルまたは環境変数
- 利用制限の確認: [Google AI Studio](https://aistudio.google.com/)

## 📝 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照

## 🤝 コントリビューション

プルリクエスト歓迎です！大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 🙏 謝辞

- [Google Gemini](https://ai.google.dev/) - 高品質な音声認識API
- [Silero VAD](https://github.com/snakers4/silero-vad) - 高精度な音声区間検出
- [Obsidian](https://obsidian.md/) - 素晴らしいノートアプリ
