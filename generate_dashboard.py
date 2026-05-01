"""
Morning Financial Dashboard Auto-Generator
==========================================
Claude API を使って毎朝金融ダッシュボードを自動生成するスクリプト。

使い方:
  1. .env ファイルに ANTHROPIC_API_KEY を設定
  2. python generate_dashboard.py を実行
  3. output/ フォルダにHTMLが出力される

cron 例 (毎朝7時に実行):
  0 7 * * * cd /path/to/this/dir && /usr/bin/python3 generate_dashboard.py
"""

import os
import sys
import json
import base64
import smtplib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import anthropic
from dotenv import load_dotenv

# ── Setup ──
load_dotenv()
JST = timezone(timedelta(hours=9))
TODAY = datetime.now(JST)
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_JP = TODAY.strftime("%Y年%m月%d日")
WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"][TODAY.weekday()]

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"financial-dashboard-{DATE_STR}.html"

# ── Skill prompt (compact version of SKILL.md) ──
SYSTEM_PROMPT = """あなたはプロの金融アナリストアシスタントです。ただし、登録された金融商品取引業者ではないため、特定銘柄の「買い推奨」は断定せず、公開アナリスト見解の整理として情報を提供してください。

## タスク
今日の日付に合わせた金融特化ダッシュボードのHTMLを生成してください。

## 必須セクション
1. ヘッダー（日付、曜日、JST時刻）
2. ⚠️ 免責事項バナー（黄色）
3. 5つのティッカーカード: 日経平均、NYダウ、S&P 500、USD/JPY、ビットコイン（円建表示）
4. メインチャート（クリック切替、1M/3M/6M、Chart.js使用）
5. 1ヶ月評価レビュー（推奨銘柄の前回→現在評価とリターン）
6. 経済・国際ニュース（為替、金融政策、米国経済、暗号資産など）
7. 注目銘柄ウォッチリスト（🇯🇵日本株 / 🇺🇸米国株 タブ切替）
8. 注目ETF・投資信託
9. 注目セクター（日米統合）
10. 来週の重要経済イベント

## デザイン仕様
- ダークテーマ（Bloomberg Terminal風）
- フォント: Noto Sans JP + DM Mono + Shippori Mincho
- カラー: --bg #090e17, --card #131e2b, --accent #3b8eea, --green #34d399, --red #f87171, --orange #fb923c (BTC), --cyan #22d3ee (米国株)
- 2カラムレイアウト: 左 3fr (チャート+レビュー+ニュース) / 右 2fr (ウォッチリスト+ETF+セクター+イベント)

## チャート実装
- Chart.js 4.4.1 を CDN から読み込み
- genWalk(start, end, vol, seed, n=180) 関数で180日分のデータを生成
- 最終値は実際の現在値で固定
- すべてのティッカー・ウォッチリスト・レビュー銘柄をクリックで切替可能に
- 統計バー（始値・高値・安値・現在値・騰落率）

## 銘柄選定（現在のマーケット状況に基づく）
日本株: 三菱UFJ(8306)、東京エレクトロン(8035)、伊藤忠商事(8001)、第一生命HD(8750)、安川電機(6506)、太陽誘電(6976)、日本製鉄(5401)、日本郵船(9101)、花王(4452)、三菱HCキャピタル(8593)
米国株: NVIDIA(NVDA)、Microsoft(MSFT)、Alphabet(GOOGL)、Broadcom(AVGO)、Apple(AAPL)、Meta(META)、Tesla(TSLA)、TSMC(TSM)、Micron(MU)
ETF: TOPIX ETF(1306)、SPDRゴールド(1326)、Invesco QQQ、Vanguard S&P 500(VOO)、eMAXIS Slim 全世界株

## 出力ルール
- 完全な単一HTMLファイル（外部CSS/JS不要、CDNのみOK）
- web_search で最新の市況データを取得して反映
- 株価・為替・BTC・主要ニュースは必ず web_search で当日データを取得
- ヘッダー、本文、フッターまで省略せず完全なHTMLを出力
- 出力は **```html ... ``` で囲んだコードブロックのみ**、他の説明文は不要
"""

USER_PROMPT = f"""今日（{DATE_JP} {WEEKDAY_JP}曜日）の金融ダッシュボードのHTMLを生成してください。

以下のステップで進めてください:
1. web_search で日経平均、NYダウ、S&P 500、USD/JPY、ビットコイン の最新終値を取得
2. web_search で当日の経済・国際ニュース上位5-6件を取得
3. web_search で米国株・日本株の注目銘柄の最新動向を確認
4. すべての情報を統合して、完全な単一HTMLファイルを生成

出力は **```html で始まり ``` で終わるコードブロックのみ** にしてください。"""


def generate_dashboard():
    """Claude API で HTML を生成"""
    print(f"📊 ダッシュボード生成開始: {DATE_JP}")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY が .env に設定されていません")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("🔍 Claude が web_search で市況データを収集中...")
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=32000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_PROMPT}],
        tools=[{
            "type": "web_search_20260209",
            "name": "web_search",
            "max_uses": 12,  # 株・為替・ニュース等の検索回数上限
        }],
    )

    # ── HTML を抽出 ──
    full_text = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            full_text += block.text

    # ```html ... ``` を抽出
    if "```html" in full_text:
        html = full_text.split("```html", 1)[1]
        html = html.rsplit("```", 1)[0].strip()
    elif "```" in full_text:
        html = full_text.split("```", 1)[1]
        html = html.rsplit("```", 1)[0].strip()
    else:
        html = full_text.strip()

    if not html.startswith("<!DOCTYPE") and not html.startswith("<html"):
        print("⚠️  警告: HTML として認識できない出力です")
        print(full_text[:500])
        sys.exit(1)

    # ── 保存 ──
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"✅ 生成完了: {OUTPUT_FILE}")
    print(f"   サイズ: {len(html):,} 文字")

    # 使用量レポート
    if hasattr(response, "usage"):
        u = response.usage
        in_tok = getattr(u, "input_tokens", 0)
        out_tok = getattr(u, "output_tokens", 0)
        ws_count = getattr(u, "server_tool_use", {}).get("web_search_requests", "?") if isinstance(getattr(u, "server_tool_use", None), dict) else "?"
        print(f"   トークン: 入力 {in_tok:,} / 出力 {out_tok:,}")
        print(f"   Web検索回数: {ws_count}")

    return OUTPUT_FILE


def send_email(html_path: Path):
    """生成したHTMLをメール添付で送信（オプション）"""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    mail_to = os.getenv("MAIL_TO")

    if not all([smtp_host, smtp_user, smtp_pass, mail_to]):
        print("📧 メール送信はスキップ（SMTP設定なし）")
        return

    msg = MIMEMultipart()
    msg["Subject"] = f"📊 Financial Dashboard {DATE_JP}"
    msg["From"] = smtp_user
    msg["To"] = mail_to

    body = f"""おはようございます☀️

{DATE_JP}（{WEEKDAY_JP}曜日）の金融ダッシュボードを添付します。

ファイルをブラウザで開くと、株価チャート・注目銘柄・経済ニュースなどが表示されます。

⚠️ 投資判断はご自身の責任でお願いします。
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open(html_path, "rb") as f:
        att = MIMEApplication(f.read(), _subtype="html")
        att.add_header("Content-Disposition", "attachment", filename=html_path.name)
        msg.attach(att)

    print(f"📧 メール送信中: {mail_to}")
    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(msg)
    print("✅ メール送信完了")


def main():
    try:
        html_path = generate_dashboard()
        send_email(html_path)  # 設定があれば送信、なければスキップ
        print("\n🎉 すべて完了しました！")
    except anthropic.APIError as e:
        print(f"❌ Anthropic API エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
