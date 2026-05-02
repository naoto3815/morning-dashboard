import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv()
JST = timezone(timedelta(hours=9))
TODAY = datetime.now(JST)
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_JP = TODAY.strftime("%Y年%m月%d日")
WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"][TODAY.weekday()]
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"financial-dashboard-{DATE_STR}.html"

DATA_PROMPT = f"""今日（{DATE_JP} {WEEKDAY_JP}曜日）の金融市況をweb_searchで調べて、以下のJSON形式だけで出力してください。説明文は不要です。

{{
  "date": "{DATE_JP}",
  "weekday": "{WEEKDAY_JP}曜日",
  "nikkei": {{"value": "59513", "change": "+228", "pct": "+0.38%", "direction": "up"}},
  "dow": {{"value": "49652", "change": "+790", "pct": "+1.62%", "direction": "up"}},
  "sp500": {{"value": "7204", "change": "+73", "pct": "+1.02%", "direction": "up"}},
  "usdjpy": {{"value": "157.32", "change": "+0.38", "pct": "+0.24%", "direction": "up", "note": "介入警戒"}},
  "btc_usd": "76052",
  "btc_jpy": "11964000",
  "btc_change_pct": "-1.71%",
  "btc_direction": "down",
  "fx_rate": "157.32",
  "news": [
    {{"tag": "為替", "title": "見出し1", "body": "詳細1"}},
    {{"tag": "マーケット", "title": "見出し2", "body": "詳細2"}},
    {{"tag": "米国経済", "title": "見出し3", "body": "詳細3"}},
    {{"tag": "国際情勢", "title": "見出し4", "body": "詳細4"}},
    {{"tag": "暗号資産", "title": "見出し5", "body": "詳細5"}}
  ],
  "events": [
    {{"date": "5月7日(木)", "importance": "高", "name": "FOMC結果発表", "desc": "早朝3時。利下げ示唆に注目。"}},
    {{"date": "5月8日(金)", "importance": "高", "name": "米雇用統計", "desc": "21時30分発表。"}}
  ],
  "market_note": "マーケット短評"
}}"""

HTML_SYSTEM = """あなたはフロントエンドエンジニアです。金融データを受け取り完全なHTMLを生成します。

デザイン:
- ダークテーマ Bloomberg風
- Google Fonts: Noto Sans JP + DM Mono + Shippori Mincho
- Chart.js 4.4.1: https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js
- CSS変数: --bg:#090e17 --surface:#0f1923 --card:#131e2b --border:#1e2d3d --accent:#3b8eea --green:#34d399 --red:#f87171 --orange:#fb923c --cyan:#22d3ee --yellow:#fbbf24 --purple:#a78bfa --text:#cdd9e5 --text-dim:#7a96b0 --text-bright:#e8f0f8

レイアウト:
1. ヘッダー(日付 曜日 時計)
2. 免責事項バナー(黄色)
3. ティッカー5枚(日経 NYダウ SP500 USDJPY BTC円建)
4. 2カラム(左3fr:チャート+レビュー+ニュース 右2fr:ウォッチリスト+ETF+セクター+イベント)

チャート必須実装:
- genWalk(start,end,vol,seed,n=180)でデータ生成
- DATAオブジェクトに全銘柄定義(nikkei dow sp500 forex btc d8306 d8035 d8001 d8750 d6506 d6976 d5401 d9101 d4452 d8593 dNVDA dMSFT dGOOGL dAVGO dAAPL dMETA dTSLA dTSM dMU d1306 d1326 dQQQ dVOO dOLCAN)
- 全要素にdata-key属性とonclick="switchToStock(key,this)"
- switchToStock関数でDATA[key]がない場合のフォールバック実装
- 期間ボタン1M/3M/6M
- 統計バー(始値 高値 安値 現在値 騰落率)
- 日米タブ切替ウォッチリスト
- 1ヶ月評価レビュー全行にdata-key+onclick

出力: ```html から ``` で囲んだ完全なHTMLのみ"""


def collect_data(client):
    print("Phase1: 市況データ収集中")
    result = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": DATA_PROMPT}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
    ) as stream:
        for text in stream.text_stream:
            result += text
            print(text, end="", flush=True)
    print("\nPhase1完了")
    return result


def generate_html(client, data):
    print("Phase2: HTML生成中")
    prompt = f"以下の市況データでダッシュボードHTMLを生成してください。\n\n{data}\n\n```html で始まり ``` で終わるコードのみ出力してください。"
    result = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=HTML_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            result += text
            print(".", end="", flush=True)
    print("\nPhase2完了")
    return result


def main():
    print(f"生成開始: {DATE_JP}")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY未設定")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)
    try:
        data = collect_data(client)
        raw = generate_html(client, data)
        if "```html" in raw:
            html = raw.split("```html", 1)[1].rsplit("```", 1)[0].strip()
        elif "```" in raw:
            html = raw.split("```", 1)[1].rsplit("```", 1)[0].strip()
        else:
            html = raw.strip()
        if not (html.startswith("<!DOCTYPE") or html.startswith("<html")):
            print("警告: HTML形式として認識できません")
            print(raw[:300])
            sys.exit(1)
        OUTPUT_FILE.write_text(html, encoding="utf-8")
        print(f"保存完了: {OUTPUT_FILE} ({len(html)}文字)")
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
