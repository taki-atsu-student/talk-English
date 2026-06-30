# Talk English Tutor - セットアップガイド

English | [日本語](SETUP_JA.md)

## 📋 前提条件

- Python 3.10+
- Node.js 16+ (Frontend development)
- Git
- 4GB+ RAM (推奨 GPU メモリ: 8GB+)
- インターネット接続

## 🚀 クイックスタート

### 1. リポジトリをクローン

```bash
git clone https://github.com/YOUR_USERNAME/talk-English.git
cd talk-English
```

### 2. 環境設定ファイルをコピー

```bash
# Backend
cp .env.example .env

# Frontend
cp frontend/.env.example frontend/.env
```

### 3. Backend セットアップ

#### 3.1 仮想環境作成（推奨）

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### 3.2 依存関係インストール

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

**⚠️ GPU 利用の場合** (CUDA):

```bash
# NVIDIA GPU の場合
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Frontend セットアップ

```bash
cd frontend
npm install
# または
yarn install
```

### 5. 起動方法

#### 方法 A: Backend API + Web UI (推奨)

```bash
# Terminal 1: Backend を起動
python backend/main.py
# または
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで `http://localhost:8000` にアクセス

#### 方法 B: CLI チャット (テスト用)

```bash
python backend/chat.py
```

#### 方法 C: Frontend 単体開発

```bash
cd frontend
npm start
```

## 📁 ディレクトリ構造

```
talk-English/
├── backend/
│   ├── main.py              # FastAPI メイン (Web UI + API)
│   ├── chat.py              # CLI テスト用
│   ├── requirements.txt      # Python 依存関係
│   ├── static/
│   │   └── index.html       # Web UI
│   └── CHAT_SCRIPT_README.md
├── frontend/                # React Native/Expo
│   ├── package.json
│   ├── tsconfig.json
│   ├── .eslintrc.json
│   └── assets/
├── talk-english-tutor/      # Hugging Face Spaces デプロイ
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── .gitignore
├── .env.example
├── Dockerfile               # Docker コンテナ化
├── README.md
└── setup_device.*          # セットアップ補助スクリプト
```

## 🧪 テスト実行

### Unit テスト

```bash
cd frontend
npm run test
```

### リント・型チェック

```bash
# ESLint
npm run lint

# TypeScript 型チェック
npm run type-check
```

### API エンドポイント確認

```bash
# API ドキュメント (Swagger UI)
http://localhost:8000/docs

# Health チェック
curl http://localhost:8000/health
```

## 🐳 Docker での実行

### ローカルビルド & 実行

```bash
docker build -t talk-english:latest .
docker run -p 8000:8000 talk-english:latest
```

### Hugging Face Spaces へデプロイ

```bash
# Dockerfile は既に用意されています
# Hugging Face Spaces の Web UI から直接デプロイ可能
```

詳細: [talk-english-tutor/README.md](talk-english-tutor/README.md)

## 🔧 環境変数設定

### Backend (.env)

```env
BACKEND_PORT=8000
MODEL_NAME=microsoft/DialoGPT-small
GRAMMAR_TOOL_LANGUAGE=en-US
DEPLOYMENT_ENV=development
```

### Frontend (.env.local)

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_TITLE=Talk English Tutor
REACT_APP_DEBUG_MODE=true
```

## 📊 パフォーマンスチューニング

### メモリ不足の場合

```python
# backend/main.py の model_name を変更
MODEL_NAME = "microsoft/DialoGPT-small"  # 軽量版
```

### 高速化

- GPU 利用: CUDA インストール
- モデルキャッシング: 2 回目以降の起動は高速
- 静的ファイルキャッシング: ブラウザキャッシュ活用

## 🐛 トラブルシューティング

### モデル読み込みエラー

```
OSError: Can't load '...'
```

**解決策:**

```bash
# キャッシュクリア
pip cache purge

# 再インストール
pip install --force-reinstall transformers
```

### ポート競合エラー

```bash
# 別のポートで起動
uvicorn backend.main:app --port 8001
```

### メモリ不足

- バックグラウンドプロセス終了
- `requirements.txt` から不要な依存関係を削除
- より小さいモデルを利用

### GPU が認識されない

```bash
# 確認
python -c "import torch; print(torch.cuda.is_available())"

# CUDA 11.8 との同期
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## 📚 さらに学ぶ

- [README.md](README.md) - プロジェクト概要
- [backend/CHAT_SCRIPT_README.md](backend/CHAT_SCRIPT_README.md) - CLI スクリプト詳細
- [talk-english-tutor/README.md](talk-english-tutor/README.md) - デプロイメント

## 🤝 貢献

プルリクエストを歓迎します！

## 📄 ライセンス

[MIT License](LICENSE)

---

**質問・問題がありましたら、Issues を作成してください！**
