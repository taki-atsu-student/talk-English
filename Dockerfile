FROM python:3.10-slim

WORKDIR /app

# 依存関係インストール（backend/requirements.txt を使用）
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリコード
COPY backend/main.py app.py
COPY backend/static ./static

# ポート公開（バックエンドはデフォルトで 8000 を使用）
EXPOSE 8000

# アプリ起動
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
