"""
Morning Financial Dashboard Auto-Generator (2段階生成版)
Phase 1: web_search で市況データを収集
Phase 2: 収集データを元にHTML生成
"""
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

DATA_COLLECTION_PROMPT = f"""今日（{DATE_JP} {WEEKDAY_JP}曜日）の金融市況データをweb_searchで収集し、以下のJSON形式のみで出力してください（説明文不要）:

{{
  "date": "{DATE_JP}",
  "weekday": "{WEEKDAY_JP}曜日",
  "nikkei": {{"value": "59,513", "change": "+228.00", "pct": "+0.38%", "direction": "up"}},
  "dow": {{"value": "49,652", "change": "+790.33", "pct": "+1.62%", "direction": "up"}},
  "sp500": {{"value": "7,204", "change": "+73.06", "pct": "+1.02%", "direction": "up"}},
  "usdjpy": {{"value": "157.32", "change": "+0.38", "pct": "+0.24%", "direction": "up", "note": "介入警戒"}},
  "btc_usd": "76,052",
  "btc_jpy": "11,964,000",
  "btc_change_pct": "-1.71%",
  "btc_direction": "down",
  "fx_rate": "157.32",
  "news": [
    {{"tag": "為替", "title": "見出し", "body": "詳細"}},
    {{"tag": "マーケット", "title": "見出し", "body": "詳細"}},
    {{"tag": "米国経済", "title": "見出し", "body": "詳細"}},
    {{"tag": "国際情勢", "title": "見出し", "body": "詳細"}},
    {{"tag": "暗号資産", "title": "見出し", "body": "詳細"}}
  ],
  "events": [
    {{"date": "5月7日(木)", "importance": "高", "name": "FOMC結果発表", "desc": "早朝3:00。利下げ示唆の有無に注目。"}},
    {{"date": "5月8日(金)", "importance": "高", "name": "米雇用統計(4月)", "desc": "21:30発表。"}}
  ],
  "market_note": "マーケット短評1〜2文"
}}

上記JSONの値を実際の今日のデータに置き換えて出力してください。"""

HTML_SYSTEM_PROMPT = """あなたはフロントエンドエンジニアです。金融データを受け取り、完全なHTMLダッシュボードを生成します。

## デザイン
- ダークテーマ、Bloomberg Terminal風
- Google Fonts: Noto Sans JP + DM Mono + Shippori Mincho
- Chart.js 4.4.1: https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js
- CSS変数: --bg:#090e17, --surface:#0f1923, --card:#131e2b, --border:#1e2d3d, --accent:#3b8eea, --green:#34d399, --red:#f87171, --orange:#fb923c, --cyan:#22d3ee, --yellow:#fbbf24, --purple:#a78bfa, --text:#cdd9e5, --text-dim:#7a96b0, --text-bright:#e8f0f8

## レイアウト
1. ヘッダー（日付・曜日・リアルタイム時計 setInterval毎秒更新）
2. 免責事項バナー（黄色背景）
3. ティッカーカード5枚横並び（日経・NYダウ・S&P500・USD/JPY・BTC円建）
4. 2カラム（左3fr: チャート+レビュー+ニュース / 右2fr: ウォッチリスト+ETF+セクター+イベント）

## チャート（必須・省略禁止）
```javascript
// 必ずこの構造で実装すること
function sr(seed){let s=seed;return()=>{s=(s*9301+49297)%233280;return s/233280;};}
function genWalk(start,end,vol,seed,n=180){
  const r=sr(seed);const inc=Array.from({length:n-1},()=>(r()-0.5)*2*vol);
  let cum=0;const raw=[start];
  for(let i=0;i<n-1;i++){cum+=inc[i];raw.push(start+cum);}
  const drift=(end-(start+cum))/(n-1);
  const corrected=raw.map((v,i)=>+(v+drift*i).toFixed(2));
  corrected[n-1]=end;return corrected;
}

// DATAオブジェクト（全銘柄必須）
const DATA = {
  nikkei:{label:'日経平均',code:'N225',data:genWalk(38000,59513,800,1),color:'#34d399',pre:'',fmt:v=>Math.round(v).toLocaleString()},
  dow:   {label:'NYダウ',code:'DJIA',data:genWalk(43000,49652,550,2),color:'#3b8eea',pre:'',fmt:v=>Math.round(v).toLocaleString()},
  sp500: {label:'S&P 500',code:'SPX',data:genWalk(5800,7204,90,3),color:'#a78bfa',pre:'',fmt:v=>Math.round(v).toLocaleString()},
  forex: {label:'USD/JPY',code:'FX',data:genWalk(152,157.32,0.6,4),color:'#f87171',pre:'¥',fmt:v=>Number(v).toFixed(2)},
  btc:   {label:'BTC(円)',code:'BTC',data:genWalk(9000000,11964000,280000,5),color:'#fb923c',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  // 日本株
  d8306: {label:'三菱UFJ FG',code:'8306',data:genWalk(1580,1815,28,20),color:'#34d399',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d8035: {label:'東京エレクトロン',code:'8035',data:genWalk(28000,42500,650,21),color:'#34d399',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d8001: {label:'伊藤忠商事',code:'8001',data:genWalk(7200,8450,135,22),color:'#34d399',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d8750: {label:'第一生命HD',code:'8750',data:genWalk(3200,3850,55,23),color:'#34d399',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d6506: {label:'安川電機',code:'6506',data:genWalk(4100,5180,95,24),color:'#34d399',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d6976: {label:'太陽誘電',code:'6976',data:genWalk(3450,4150,72,25),color:'#34d399',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d5401: {label:'日本製鉄',code:'5401',data:genWalk(2950,3340,52,26),color:'#34d399',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d9101: {label:'日本郵船',code:'9101',data:genWalk(4500,4920,90,27),color:'#fbbf24',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d4452: {label:'花王',code:'4452',data:genWalk(6800,6420,90,28),color:'#f87171',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d8593: {label:'三菱HCキャピタル',code:'8593',data:genWalk(1080,1185,18,29),color:'#34d399',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  // 米国株
  dNVDA: {label:'NVIDIA',code:'NVDA',data:genWalk(110,182,3.2,30),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dMSFT: {label:'Microsoft',code:'MSFT',data:genWalk(420,484,7,31),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dGOOGL:{label:'Alphabet',code:'GOOGL',data:genWalk(178,225,3.8,32),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dAVGO: {label:'Broadcom',code:'AVGO',data:genWalk(220,288,5.5,33),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dAAPL: {label:'Apple',code:'AAPL',data:genWalk(218,235,3.6,34),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dMETA: {label:'Meta',code:'META',data:genWalk(620,712,12,35),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dTSLA: {label:'Tesla',code:'TSLA',data:genWalk(298,265,9,36),color:'#f87171',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dTSM:  {label:'TSMC',code:'TSM',data:genWalk(178,228,4.2,37),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dMU:   {label:'Micron',code:'MU',data:genWalk(380,455,9.5,38),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  // ETF
  d1306: {label:'TOPIX ETF',code:'1306',data:genWalk(2900,3680,42,40),color:'#3b8eea',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  d1326: {label:'SPDRゴールド',code:'1326',data:genWalk(48000,55200,650,41),color:'#fbbf24',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
  dQQQ:  {label:'Invesco QQQ',code:'QQQ',data:genWalk(485,548,9,42),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dVOO:  {label:'Vanguard S&P500',code:'VOO',data:genWalk(540,615,8,43),color:'#22d3ee',pre:'$',fmt:v=>Number(v).toFixed(2)},
  dOLCAN:{label:'eMAXIS Slim全世界株',code:'OLCAN',data:genWalk(28500,32400,360,44),color:'#a78bfa',pre:'¥',fmt:v=>Math.round(v).toLocaleString()},
};

// switchToStock（全銘柄共通）
function switchToStock(key, el){
  if(!DATA[key]){console.warn('key not found:',key);return;}
  currentKey=key;
  document.querySelectorAll('[data-key]').forEach(t=>t.classList.remove('active-stock'));
  document.querySelectorAll('[data-key="'+key+'"]').forEach(t=>t.classList.add('active-stock'));
  buildMain(key,currentRange);
  document.getElementById('mainChart').scrollIntoView({behavior:'smooth',block:'nearest'});
}
```

## ウォッチリスト
- 日本株・米国株タブ切替
- 各行: `<div class="wl-item" data-key="dNVDA" onclick="switchToStock('dNVDA',this)">`
- 1ヶ月レビューも同様に全行にdata-key+onclick付与

## 出力ルール
- <!DOCTYPE html>から</html>まで完全なHTML
- ```html コードブロックで囲む"""


def collect_market_data(client):
    print("🔍 Phase 1: 市況データ収集中...")
    result = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": DATA_COLLECTION_PROMPT}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
    ) as stream:
        for text in stream.text_stream:
            result += text
            print(text, end="", flush=True)
    print("\n✅ 収集完了")
    return result


def generate_html(client, market_data):
    print("\n🎨 Phase 2: HTML生成中...")
    user_prompt = f"""以下の市況データでダッシュボードHTMLを生成してください。

## 本日の市況データ
{market_data}

必ずDATAオブジェクトにすべての銘柄を定義し、全ウォッチリスト・レビュー銘柄にdata-key属性とonclickを付与してください。
```html で始まり ``` で終わるコードブロックで出力してください。"""

    result = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=HTML_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            result += text
            print(".", end="", flush=True)
    print("\n✅ HTML生成完了")
    return result


def main():
    print(f"📊 生成開始: {DATE_JP} {WEEKDAY_JP}曜日")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY が未設定です")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    try:
        market_data = collect_market_data(client)
        raw_output = generate_html(client, market_data)

        if "```html" in raw_output:
            html = raw_output.split("```html", 1)[1].rsplit("```", 1)[0].strip()
        elif "```" in raw_output:
            html = raw_output.split("```", 1)[1].rsplit("```", 1)[0].strip()
        else:
            html = raw_output.strip()

        if not (html.startswith("<!DOCTYPE") or html.startswith("<html")):
            print("⚠️ HTML形式として認識できません")
            print(raw_output[:300])
            sys.exit(1)

        OUTPUT_FILE.write_text(html, encoding="utf-8")
        print(f"\n✅ 保存: {OUTPUT_FILE} ({len(html):,}文字)")
        print("🎉 完了！")

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---



---

ちなみに、GitHub Pages の設定はもう済んでいますか？URLが `https://naoto3815.github.io/morning-dashboard/` で確定したなら、**今すぐカレンダーにリマインダーを登録**しておきましょうか？
