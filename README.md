# talk-English

Talk English Tutor は、FastAPI と外部 AI API を使った英語学習チャットアプリです。
このアプリはブラウザ UI と API 連携にフォーカスし、ローカルで大きなモデルを実行しません。

## 概要

- ユーザーは `backend/static/index.html` からブラウザで英語メッセージを送信します。
- バックエンドは Groq API を呼び出し、応答と文法フィードバックを生成します。
- モバイルでも使いやすい、シンプルなチャット UI を提供します。

## 使い方

1. ルートの `.env` に `GROQ_API_KEY` を設定します。
2. `run_backend.bat` を実行してバックエンドを起動します。
3. ブラウザで `http://localhost:8000/static/index.html` にアクセスします。
4. 英語メッセージを入力して AI と会話を始めます。

## API

- `POST /chat`
  ```json
  { "text": "Hello, I want to practice English." }
  ```
- 返却される JSON の例:
  ```json
  {
    "response": "Sure! Let's practice together.",
    "session_id": "...",
    "timestamp": "2026-07-01T12:00:00",
    "feedback": "💡 Tip: ..."
  }
  ```

- `POST /translate`
  ```json
  { "text": "Hello world" }
  ```
- `GET /health` でサーバー状態を確認できます。

## バックエンド

- `backend/main.py` : FastAPI API サーバー
- `backend/requirements.txt` : Python 依存関係
- `backend/static/index.html` : フロントエンド UI

## 特長

- ダークモード対応
- 翻訳ボタン
- リアルタイム入力フィードバック
- エラー時リトライ
- 優しい英文法アドバイス

## 注意

- `.env` の `GROQ_API_KEY` を必ず設定してください。
- `backend/static/index.html` はこのリポジトリの主要なフロントエンドです。
- 古い `frontend/` や `talk-english-tutor/` は現在の利用フローに含まれません。

## ローカルでの実行（Quick Start）

1. ルートに `.env` を作成し、`GROQ_API_KEY` を設定します。

2. 仮想環境がある場合は有効化してください（任意）:

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

3. 依存をインストールします:

```powershell
python -m pip install -r backend\requirements.txt
```

4. サーバーを起動します:

```powershell
.\n+run_backend.bat
```

5. ブラウザで `http://localhost:8000/static/index.html` を開きます。

6. テストを実行する場合:

```powershell
python -m pytest backend -q
```

問題があれば、`backend/main.py` と `backend/static/index.html` を確認してください。
