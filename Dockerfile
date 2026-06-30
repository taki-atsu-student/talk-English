FROM python:3.10-slim

WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリコード
COPY backend/main.py app.py
COPY backend/static ./static

# ポート公開
EXPOSE 7860

# アプリ起動
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
