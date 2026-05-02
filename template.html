import os, sys, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv()
JST = timezone(timedelta(hours=9))
TODAY = datetime.now(JST)
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_JP = TODAY.strftime("%Y年%m月%d日")
WEEKDAY_JP = ["月","火","水","木","金","土","日"][TODAY.weekday()]
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"financial-dashboard-{DATE_STR}.html"
TEMPLATE_FILE = Path(__file__).parent / "template.html"

DATA_PROMPT = """今日の金融市況をweb_searchで調べ、以下のJSONのみ出力してください。説明文不要。

{
  "nikkei_val":"59513","nikkei_chg":"+228","nikkei_pct":"+0.38%","nikkei_dir":"up",
  "dow_val":"49652","dow_chg":"+790","dow_pct":"+1.62%","dow_dir":"up",
  "sp500_val":"7204","sp500_chg":"+73","sp500_pct":"+1.02%","sp500_dir":"up",
  "usdjpy_val":"157.32","usdjpy_chg":"+0.38","usdjpy_dir":"up","usdjpy_note":"介入警戒",
  "btc_jpy":"11964000","btc_usd":"76052","btc_pct":"-1.71%","btc_dir":"down",
  "gold_val":"3280","oil_val":"100.12","eurjpy_val":"169.84",
  "news":[
    {"tag":"為替","title":"見出し1","body":"詳細1"},
    {"tag":"マーケット","title":"見出し2","body":"詳細2"},
    {"tag":"米国経済","title":"見出し3","body":"詳細3"},
    {"tag":"国際情勢","title":"見出し4","body":"詳細4"},
    {"tag":"暗号資産","title":"見出し5","body":"詳細5"}
  ],
  "events":[
    {"date":"5月7日","weekday":"木","imp":"高","name":"FOMC結果発表","desc":"早朝3時。利下げ示唆に注目。"},
    {"date":"5月8日","weekday":"金","imp":"高","name":"米雇用統計(4月)","desc":"21時30分発表。"},
    {"date":"5月28日","weekday":"水","imp":"高","name":"NVIDIA決算","desc":"AI関連株の方向性を決める。"}
  ]
}

実際の今日のデータに置き換えて出力してください。"""


def collect_data(client):
    print("Phase1: 市況データ収集中...")
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


def parse_data(raw):
    match = re.search(r'\{[\s\S]*\}', raw)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except Exception:
        return {}


def g(d, key, default=""):
    return str(d.get(key, default))


def news_html(items):
    if not items:
        return '<div class="ni"><div class="nt">情報</div><div class="nb">データ取得中...</div></div>'
    rows = []
    for n in items:
        rows.append(
            '<div class="ni">'
            '<div class="nt">' + n.get("tag","") + '</div>'
            '<div class="nb"><strong>' + n.get("title","") + '</strong>'
            + (' — ' + n.get("body","") if n.get("body") else "") +
            '</div></div>'
        )
    return "\n".join(rows)


def events_html(items):
    if not items:
        return ""
    rows = []
    for e in items:
        imp = e.get("imp","中")
        tc = "et" if imp == "高" else "et et-mid"
        rows.append(
            '<div class="ei">'
            '<div class="ed">' + e.get("date","") + '<br><span style="font-size:14px;color:var(--text-bright)">' + e.get("weekday","") + '</span></div>'
            '<div><div class="en"><span class="' + tc + '">' + imp + '</span>' + e.get("name","") + '</div>'
            '<div class="edesc">' + e.get("desc","") + '</div></div>'
            '</div>'
        )
    return "\n".join(rows)


def main():
    print("生成開始:", DATE_JP)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY未設定")
        sys.exit(1)

    if not TEMPLATE_FILE.exists():
        print("エラー: template.html が見つかりません。リポジトリに template.html を追加してください。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    try:
        raw = collect_data(client)
        d = parse_data(raw)

        def v(key, default):
            return str(d.get(key, default))

        nikkei_dir = v("nikkei_dir","up")
        dow_dir    = v("dow_dir","up")
        sp500_dir  = v("sp500_dir","up")
        usdjpy_dir = v("usdjpy_dir","up")
        btc_dir    = v("btc_dir","down")

        def badge(direction):
            return "b-up" if direction == "up" else "b-dn"
        def arrow(direction):
            return "▲" if direction == "up" else "▼"
        def dircls(direction):
            return "up" if direction == "up" else "dn"
        def num(s):
            return s.replace(",","").replace("+","").strip()

        btc_jpy = v("btc_jpy","11964000")
        try:
            btc_jpy_fmt = "{:,}".format(int(num(btc_jpy)))
        except Exception:
            btc_jpy_fmt = btc_jpy

        nikkei_val = v("nikkei_val","59513")
        dow_val    = v("dow_val","49652")
        sp500_val  = v("sp500_val","7204")
        usdjpy_val = v("usdjpy_val","157.32")

        template = TEMPLATE_FILE.read_text(encoding="utf-8")

        replacements = {
            "__DATE_JP__":      DATE_JP,
            "__WEEKDAY_JP__":   WEEKDAY_JP,
            "__NIKKEI_VAL__":   nikkei_val,
            "__NIKKEI_CHG__":   v("nikkei_chg","+228"),
            "__NIKKEI_PCT__":   v("nikkei_pct","+0.38%"),
            "__NIKKEI_DIR__":   dircls(nikkei_dir),
            "__NIKKEI_BADGE__": badge(nikkei_dir),
            "__NIKKEI_ARROW__": arrow(nikkei_dir),
            "__NIKKEI_NUM__":   num(nikkei_val),
            "__DOW_VAL__":      dow_val,
            "__DOW_CHG__":      v("dow_chg","+790"),
            "__DOW_PCT__":      v("dow_pct","+1.62%"),
            "__DOW_DIR__":      dircls(dow_dir),
            "__DOW_BADGE__":    badge(dow_dir),
            "__DOW_ARROW__":    arrow(dow_dir),
            "__DOW_NUM__":      num(dow_val),
            "__SP500_VAL__":    sp500_val,
            "__SP500_CHG__":    v("sp500_chg","+73"),
            "__SP500_PCT__":    v("sp500_pct","+1.02%"),
            "__SP500_DIR__":    dircls(sp500_dir),
            "__SP500_BADGE__":  badge(sp500_dir),
            "__SP500_ARROW__":  arrow(sp500_dir),
            "__SP500_NUM__":    num(sp500_val),
            "__USDJPY_VAL__":   usdjpy_val,
            "__USDJPY_CHG__":   v("usdjpy_chg","+0.38"),
            "__USDJPY_DIR__":   dircls(usdjpy_dir),
            "__USDJPY_BADGE__": badge(usdjpy_dir),
            "__USDJPY_ARROW__": arrow(usdjpy_dir),
            "__USDJPY_NOTE__":  v("usdjpy_note","介入警戒"),
            "__USDJPY_NUM__":   num(usdjpy_val),
            "__BTC_JPY_FMT__":  btc_jpy_fmt,
            "__BTC_JPY_NUM__":  num(btc_jpy),
            "__BTC_USD__":      v("btc_usd","76052"),
            "__BTC_PCT__":      v("btc_pct","-1.71%"),
            "__BTC_DIR__":      dircls(btc_dir),
            "__BTC_BADGE__":    badge(btc_dir),
            "__BTC_ARROW__":    arrow(btc_dir),
            "__GOLD_VAL__":     v("gold_val","3280"),
            "__OIL_VAL__":      v("oil_val","100.12"),
            "__EURJPY_VAL__":   v("eurjpy_val","169.84"),
            "__NEWS_HTML__":    news_html(d.get("news",[])),
            "__EVENTS_HTML__":  events_html(d.get("events",[])),
        }

        html = template
        for k, val in replacements.items():
            html = html.replace(k, val)

        OUTPUT_FILE.write_text(html, encoding="utf-8")
        print("保存完了:", OUTPUT_FILE, "(" + str(len(html)) + "文字)")
        print("完了!")

    except Exception as e:
        print("エラー:", e)
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
