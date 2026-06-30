# chat.py - CLI Testing Script for Talk English Tutor

## 概要

`chat.py` は、FastAPI サーバーを起動せずに、**ローカル CLI 環境で英語学習チャットをテストするためのスクリプト**です。

### 用途

- 🧪 **開発・デバッグ**: モデル動作確認
- 📝 **オフラインテスト**: サーバーなしで快速テスト
- 🎓 **スタンドアロン利用**: CLI ツールとして直接実行

## 使い方

### 前提条件

```bash
pip install -r backend/requirements.txt
```

### 実行

```bash
python backend/chat.py
```

### 対話例

```
AI: Hello! I'm here to help you practice English at a master level. I'll automatically check your grammar and explain in Japanese.

You: I goes to school
✗ Grammar check: ...

You: exit
```

## 特徴

- ✅ **即座に文法チェック**: language-tool-python で素早く指摘
- ✅ **日本語説明**: 文法エラーは日本語で分かりやすく表示
- ✅ **会話履歴**: 直近の会話コンテキストで応答精度向上
- ✅ **トークン最適化**: メモリ効率を重視した設定

## 構造

```
User: "I goes to school"
  ↓
Grammar Checker (language_tool_python) → 文法エラー指摘 (日本語)
  ↓
Conversation History (直近 50 トークン保持)
  ↓
DialoGPT-large → AI 応答生成
  ↓
Output: "I see. The correct form is 'I go to school'. Let me help..."
```

## トラブルシューティング

### 起動が遅い場合

- 初回起動時: モデル・文法チェッカーのダウンロードが実行されます（数分かかることあり）
- 2 回目以降: キャッシュから読み込まれます

### メモリ不足エラー

GPU メモリが不足している場合、`model_name` を小さいモデルに変更：

```python
# 現在
model_name = "microsoft/DialoGPT-large"

# 軽量版に変更
model_name = "microsoft/DialoGPT-small"
```

## 本番環境との違い

| 項目 | chat.py (CLI) | backend/main.py (FastAPI) |
|------|---------------|---------------------------|
| インターフェース | コマンドライン | Web UI + API |
| モデルサイズ | DialoGPT-large | DialoGPT-small |
| 文法チェック | LLM 統合チェック | language-tool-python |
| 会話履歴 | 直近 50 トークン | 直近 20 メッセージ |
| デプロイ | ローカルのみ | サーバー・コンテナ対応 |

## 開発フロー

1. **新機能開発**: `chat.py` で CLI テスト
2. **API 化**: 実装を `backend/main.py` に統合
3. **Web UI テスト**: ブラウザで動作確認
4. **本番デプロイ**: Docker/Hugging Face Spaces へ

---

**推奨用途**: ローカル開発・デバッグ用。本番環境では `backend/main.py` を利用してください。
