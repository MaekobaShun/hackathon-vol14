# ひらめきリレー / Hirameki Relay

アイデアの種をつなぎ、誰かの発想を次へリレーするハッカソン向け実験アプリケーションです。  
Flask + Supabase (PostgreSQL) をバックエンドに、Cloudinary でユーザーアイコンを扱いながら、以下の機能を提供します。

- ユーザー登録 / ログイン
- アイデア投稿・閲覧
- アイデアガチャ（他ユーザーの投稿をランダムに取得）
- マイページでの履歴閲覧・プロフィール編集

## 技術スタック

- Python 3.13 / Flask 2.2
- Supabase (PostgreSQL 15) – データ永続化
- Cloudinary – 画像アップロード（アイコン）
- Render – デプロイ先
- フロントエンド: Flask テンプレート + カスタム CSS

## デモ

- 本番稼働中: [https://hirameki-relay.onrender.com/](https://hirameki-relay.onrender.com/)

- 画面操作デモ GIF:
![アプリ操作デモ](relay/static/uploads/demo.gif)

## セットアップ

### 1. リポジトリの取得

```bash
git clone https://github.com/your-org/hackathon-vol14.git
cd hackathon-vol14
```

### 2. Python 環境の準備

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 環境変数

`.env` などに以下を設定してください（Render 環境でも同名の環境変数を登録します）。

| 変数名 | 説明 |
| --- | --- |
| `SECRET_KEY` | Flask セッション用シークレット |
| `SUPABASE_DATABASE_URL` | Supabase の Session Pooler など IPv4 対応接続文字列<br>`postgresql://user:pass@host:6543/dbname` |
| `UPLOAD_FOLDER` | アイコン保存先（Cloudinary を使う場合は fallback のみ）例: `/opt/render/project/src/static/uploads` |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Cloudinary を利用する場合に必須 |
| `CLOUDINARY_UPLOAD_FOLDER` | 任意。Cloudinary 上のフォルダ名 |

※ Supabase に直接接続する場合は `SUPABASE_HOST`, `SUPABASE_PORT`, `SUPABASE_DB`, `SUPABASE_USER`, `SUPABASE_PASSWORD` の組み合わせでも可。  
※ 環境変数が不足している場合は自動的にローカル SQLite (`database.db`) を利用します。

### 4. Supabase 初期化

初回は Supabase の SQL Editor で以下を実行し、PostgreSQL テーブルを作成します。

```sql
-- mypage, ideas, gacha_result, revival_notify, thanks
-- （全文は docs/sql/schema.sql を参照）
```

※ 既存の SQLite データを移行する場合は CSV などでインポートしてください。

### 5. Cloudinary

画像アップロードを有効化するには Cloudinary の認証情報を環境変数に設定します。設定が無い場合は `UPLOAD_FOLDER` に保存します。

## 開発サーバーの起動

```bash
flask --app relay.main run --debug
```

http://127.0.0.1:5000 にアクセスして動作確認します。

## デプロイ

Render を利用する場合:

1. **Build Command**: `pip install -r requirements.txt`
2. **Start Command**: `gunicorn relay.main:app`
3. 環境変数（上記）を Render ダッシュボードで設定
4. Supabase 接続は IPv4 対応の Session Pooler を利用 (`...@pooler.supabase.co:6543`)

※ 自動デプロイ（Auto Deploy）が有効な場合、対象ブランチに push すると再デプロイされます。

