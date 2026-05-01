# 📊 Morning Financial Dashboard - 自動生成システム

毎朝、Claude API + Web Search で最新の金融市況を取得し、ダッシュボードHTMLを自動生成します。

---

## 🎯 何ができるか

- 毎朝指定時刻に自動実行
- 当日の株価・為替・BTC・経済ニュースを Claude が web_search で取得
- 完成したHTMLを `output/` フォルダに保存
- （オプション）メールで自分宛に送信
- （オプション）GitHub Pages で公開URL生成

---

## 🚀 クイックスタート

### 必要なもの
- Anthropic API Key（[console.anthropic.com](https://console.anthropic.com) で取得）
- Python 3.10+
- (オプション) GitHubアカウント、Gmailアカウント

### コスト目安
- **Claude Opus 4.7**: 1回の生成で約 $0.30〜0.80（入出力トークン + web_search 12回 × $0.01）
- **月間（毎日生成）**: 約 $9〜24（≒ ¥1,400〜3,800）

---

## セットアップ手順

### 方法A: ローカルマシンで実行（macOS / Linux / Windows）

#### 1. ファイルを配置
```bash
mkdir ~/morning-dashboard
cd ~/morning-dashboard
# このフォルダに generate_dashboard.py、.env.example、requirements.txt を配置
```

#### 2. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

#### 3. .env を作成
```bash
cp .env.example .env
# .env を開いて ANTHROPIC_API_KEY を設定
```

#### 4. 動作確認
```bash
python generate_dashboard.py
# → output/financial-dashboard-YYYY-MM-DD.html が生成される
```

#### 5. スケジュール登録

**macOS / Linux (cron)**
```bash
crontab -e
# 以下を追加（毎朝7:00 JSTに実行）
0 7 * * * cd /Users/yourname/morning-dashboard && /usr/bin/python3 generate_dashboard.py >> log.txt 2>&1
```

**macOS (launchd の方が推奨)**
`~/Library/LaunchAgents/com.morning.dashboard.plist` を作成:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.morning.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/yourname/morning-dashboard/generate_dashboard.py</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/yourname/morning-dashboard</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>7</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <key>StandardOutPath</key><string>/Users/yourname/morning-dashboard/log.txt</string>
    <key>StandardErrorPath</key><string>/Users/yourname/morning-dashboard/error.txt</string>
</dict>
</plist>
```
登録:
```bash
launchctl load ~/Library/LaunchAgents/com.morning.dashboard.plist
```

**Windows（タスクスケジューラ）**
1. 「タスク スケジューラ」を開く
2. 「タスクの作成」→ トリガー：毎日 7:00
3. 操作：プログラムの開始 → `python.exe`、引数 `generate_dashboard.py`

---

### 方法B: GitHub Actions で完全クラウド実行（推奨・PCを起動しなくてOK）

#### 1. GitHubリポジトリを作成
このフォルダを GitHub にプッシュ（`.env` は除外、`.gitignore` に追加）

#### 2. Secrets を設定
リポジトリ → Settings → Secrets and variables → Actions → New repository secret

必須:
- `ANTHROPIC_API_KEY`

オプション（メール送信する場合）:
- `SMTP_HOST` = smtp.gmail.com
- `SMTP_PORT` = 587
- `SMTP_USER` = your-email@gmail.com
- `SMTP_PASS` = (Gmailアプリパスワード)
- `MAIL_TO` = your-email@gmail.com

#### 3. ワークフローを有効化
`.github/workflows/daily-dashboard.yml` がリポジトリにあれば自動で有効化されます。

#### 4. 動作確認
リポジトリ → Actions → Morning Financial Dashboard → Run workflow

毎日 22:00 UTC（= 翌7:00 JST）に自動実行されます。

#### 5. （オプション）GitHub Pages で公開URL化
リポジトリ → Settings → Pages → Source: `gh-pages` ブランチに設定
→ `https://yourname.github.io/repo-name/financial-dashboard-YYYY-MM-DD.html` でアクセス可能に

---

## 📧 メール通知の設定（オプション）

### Gmail を使う場合

1. **2段階認証を有効化**: [myaccount.google.com/security](https://myaccount.google.com/security)
2. **アプリパスワードを発行**: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. `.env` に16桁のパスワードを設定

毎朝メールで添付HTMLが届きます。

---

## 🔧 カスタマイズ

### 銘柄を変更したい
`generate_dashboard.py` の `SYSTEM_PROMPT` 内の銘柄リストを編集してください。

### 実行時刻を変更したい
- ローカル: cron / launchd の時刻設定を変更
- GitHub Actions: `.github/workflows/daily-dashboard.yml` の `cron` を変更
  - 例: 朝6時JST = 21:00 UTC前日 → `0 21 * * *`

### モデルを変えてコスト削減
`generate_dashboard.py` の `model="claude-opus-4-7"` を `claude-sonnet-4-6` に変更
→ コスト約 1/5 に削減（品質はやや低下）

---

## 🐛 トラブルシューティング

### `❌ ANTHROPIC_API_KEY が .env に設定されていません`
→ `.env.example` を `.env` にコピーして API Key を設定

### `Web search is not enabled`
→ Anthropic Console でアカウント設定から web_search を有効化

### HTML が生成されない / 切れる
→ `max_tokens` を 16000 → 32000 に増やす（料金は上がる）

### cron が動かない
- パスを絶対パスで指定（`/usr/bin/python3` など）
- `which python3` でフルパスを確認
- ログを `>> log.txt 2>&1` で出力して確認

---

## ⚠️ 免責事項

このツールが生成する情報は、AI による公開情報の整理であり、特定の銘柄を推奨するものではありません。投資判断はご自身の責任で行ってください。

---

## 📁 ファイル構成

```
morning-dashboard/
├── generate_dashboard.py      # メインスクリプト
├── requirements.txt           # Python 依存関係
├── .env.example              # 環境変数テンプレート
├── .env                      # ローカル用 (要作成・gitignore)
├── .gitignore                # 
├── README.md                 # このファイル
├── output/                   # 生成されたHTMLが保存される
└── .github/
    └── workflows/
        └── daily-dashboard.yml  # GitHub Actions 設定
```
