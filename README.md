# talk-English

ローカルで動くWeb版英語学習アプリです。

## 起動方法

1. backendフォルダに移動
   ```bash
   cd backend
   ```
2. 依存関係をインストール
   ```bash
   pip install -r requirements.txt
   ```
3. サーバーを起動
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
4. ブラウザで開く
   ```
   http://localhost:8000
   ```
