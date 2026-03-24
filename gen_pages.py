"""
日付ごとのブリーフィングHTMLを生成するスクリプト
"""
import os, json, datetime

TODAY = datetime.date.today()

with open("gijiroku_links.json", encoding="utf-8") as f:
    GIJIROKU = json.load(f)

def get_gijiroku(date_key, name):
    """date_key='2026-03-24', name='西村拓朗 x 南原竜樹' などから議事録リンクを返す"""
    gdate = date_key.replace("-", "/")
    day_data = GIJIROKU.get(gdate, {})
    # 名前の先頭4文字でマッチング
    short = name[:4]
    for key, val in day_data.items():
        if key[:4] == short or short[:len(key)] == key or key in name:
            return val
    return {"today": None, "past": None, "past_count": 0}

COLORS = [
    "linear-gradient(135deg,#1a73e8,#4285f4)",
    "linear-gradient(135deg,#ea4335,#ff6d00)",
    "linear-gradient(135deg,#9c27b0,#673ab7)",
    "linear-gradient(135deg,#00897b,#00acc1)",
    "linear-gradient(135deg,#f4511e,#ff8f00)",
    "linear-gradient(135deg,#0288d1,#0097a7)",
    "linear-gradient(135deg,#5c6bc0,#7e57c2)",
    "linear-gradient(135deg,#2e7d32,#388e3c)",
]

DAYS = {
    "2026-03-24": {
        "label": "2026年3月24日（月）",
        "zoom": [
            {"summary": "西村拓朗 x 南原竜樹", "start": "11:00", "end": "11:30",
             "zoom_url": "https://us06web.zoom.us/j/86187444034?pwd=RKoX8bbuyfudfFrGlPBZM2IYsP1ItG.1",
             "meeting_id": "861 8744 4034", "password": "599057", "message": "緊急",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"nishimuratakuro@luft-hd.co.jp","displayName":"西村拓朗","responseStatus":"accepted"}]},
            {"summary": "株式会社ウナシ　近藤 x 南原竜樹", "start": "12:30", "end": "13:00",
             "zoom_url": "https://us06web.zoom.us/j/87681817765?pwd=BbnTmh8eWaybndj6NCWW95xVkdWaw5.1",
             "meeting_id": "876 8181 7765", "password": "284127",
             "message": "対決より解決ch ディレクター候補の北澤様との三者面談",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"genaral@unashi.com","displayName":"株式会社ウナシ　近藤","responseStatus":"accepted"}]},
            {"summary": "氣仙隆造 x 南原竜樹", "start": "13:00", "end": "13:30",
             "zoom_url": "https://us06web.zoom.us/j/83517715657?pwd=HvtmiYUWtRaJHWwzZLLGhoO0jfijTy.1",
             "meeting_id": "835 1771 5657", "password": "272675",
             "message": "事業を発展させるうえで今注力すべきことを相談したいです。",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"r.kesen@bouekisupport.co.jp","displayName":"氣仙隆造","responseStatus":"accepted"}]},
            {"summary": "可児 x 南原竜樹", "start": "13:30", "end": "14:00",
             "zoom_url": "https://us06web.zoom.us/j/89401097516?pwd=gu82Z4S2oIWxz0Zac1VIBOAaDVHVR0.1",
             "meeting_id": "894 0109 7516", "password": "153420", "message": "可児です。",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"kaninaomi@luft-hd.co.jp","displayName":"可児","responseStatus":"needsAction"}]},
            {"summary": "近松虎太郎 x 南原竜樹", "start": "14:00", "end": "14:30",
             "zoom_url": "https://us06web.zoom.us/j/85983851036?pwd=EuFIYOPpszeOkTfgD6j1iHnzNSAbbI.1",
             "meeting_id": "859 8385 1036", "password": "859877", "message": "マッチングプラットフォームについて",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"k-chikamatsu@mitradata.jp","displayName":"近松虎太郎","responseStatus":"accepted"}]},
            {"summary": "古谷隆一 x 南原竜樹", "start": "14:30", "end": "15:00",
             "zoom_url": "https://us06web.zoom.us/j/81679290118?pwd=KKUNm9aOcJ2TKnaaq8nlVEJWI5NPMX.1",
             "meeting_id": "816 7929 0118", "password": "505442", "message": "ブランディング顧問について",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"global.influence.1000com@gmail.com","displayName":"古谷隆一","responseStatus":"accepted"}]},
            {"summary": "酒井信彰 x 南原竜樹", "start": "15:00", "end": "15:30",
             "zoom_url": "https://us06web.zoom.us/j/88464008458?pwd=k54Lj6Af5OCFnLrhQvJ1TrIMXGX08M.1",
             "meeting_id": "884 6400 8458", "password": "296632",
             "message": "資金調達にあたり前回、経営計画の修正をしました。",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"sakai@l-city.co.jp","displayName":"酒井信彰","responseStatus":"needsAction"}]},
            {"summary": "株式会社KINS山下 x 南原竜樹", "start": "15:30", "end": "16:00",
             "zoom_url": "https://us06web.zoom.us/j/85487870139?pwd=aChugXXWvHIg96qSxEXFNhigqh32Mx.1",
             "meeting_id": "854 8787 0139", "password": "166582", "message": "宜しくお願い致します！",
             "attendees": [{"email":"yamashita_yoshihiko@yourkins.com","displayName":"株式会社KINS山下","responseStatus":"accepted"},
                           {"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"}]},
        ]
    },
    "2026-03-25": {
        "label": "2026年3月25日（火）",
        "zoom": [
            {"summary": "Shinji Sugita x 南原竜樹", "start": "09:00", "end": "09:30",
             "zoom_url": "https://us06web.zoom.us/j/88316062126?pwd=xdJ6FomZxi7kdgyTW4gty7ULMXyypE.1",
             "meeting_id": "883 1606 2126", "password": "307610", "message": "直近発生した人材トラブルについてのご相談",
             "attendees": [{"email":"sugita@ufrcs.com","displayName":"Shinji Sugita","responseStatus":"accepted"},
                           {"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"}]},
            {"summary": "株式会社ウナシ　近藤 x 南原竜樹", "start": "15:00", "end": "15:30",
             "zoom_url": "https://us06web.zoom.us/j/83496520519?pwd=JUm86694F2UtyxGOngGT5UD0a1mSu4.1",
             "meeting_id": "834 9652 0519", "password": "309172", "message": "非属人のプレイヤーをお繋ぎする面談になります。",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"general@unashi.com","displayName":"株式会社ウナシ　近藤","responseStatus":"accepted"}]},
        ]
    },
    "2026-03-26": {
        "label": "2026年3月26日（水）",
        "zoom": []
    },
    "2026-03-27": {
        "label": "2026年3月27日（木）",
        "zoom": []
    },
    "2026-03-28": {
        "label": "2026年3月28日（金）",
        "zoom": [
            {"summary": "株式会社アンビシャスエージェント田原 章象 x 南原竜樹", "start": "12:00", "end": "12:30",
             "zoom_url": "https://us06web.zoom.us/j/87069857102?pwd=kDeHIdIbJBcxjOWxi4w654LFeH3b3p.1",
             "meeting_id": "870 6985 7102", "password": "228830", "message": "旅費規定",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"tahara@a-agent.net","displayName":"株式会社アンビシャスエージェント田原 章象","responseStatus":"accepted"}]},
            {"summary": "株式会社アンビシャスエージェント田原 章象 x 南原竜樹", "start": "12:30", "end": "13:00",
             "zoom_url": "https://us06web.zoom.us/j/83610768054?pwd=DZ4EqzhM748ZAk3xOX6heSaWDMjZa4.1",
             "meeting_id": "836 1076 8054", "password": "838129", "message": "旅費規定",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"tahara@a-agent.net","displayName":"株式会社アンビシャスエージェント田原 章象","responseStatus":"accepted"}]},
            {"summary": "氣仙隆造 x 南原竜樹", "start": "13:00", "end": "13:30",
             "zoom_url": "https://us06web.zoom.us/j/89425487957?pwd=S3aOEKl9nt6j1aluCjwHzfjB3aVms5.1",
             "meeting_id": "894 2548 7957", "password": "506489",
             "message": "3年後までの事業計画を詰めたいです。",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"r.kesen@bouekisupport.co.jp","displayName":"氣仙隆造","responseStatus":"accepted"}]},
        ]
    },
    "2026-03-29": {
        "label": "2026年3月29日（土）",
        "zoom": []
    },
    "2026-03-30": {
        "label": "2026年3月30日（日）",
        "zoom": []
    },
    "2026-03-31": {
        "label": "2026年3月31日（月）",
        "zoom": [
            {"summary": "斎藤若葉 x 南原竜樹", "start": "09:00", "end": "09:30",
             "zoom_url": "https://us06web.zoom.us/j/86316514456?pwd=QBSY5QEYuCh8g5kcAKyslNDWA9dm1h.1",
             "meeting_id": "863 1651 4456", "password": "371833", "message": "よろしくお願いします",
             "attendees": [{"email":"t.nambara.autotrading@gmail.com","responseStatus":"accepted"},
                           {"email":"wakaba02072001@gmail.com","displayName":"斎藤若葉","responseStatus":"accepted"}]},
        ]
    },
}

def make_chips(attendees):
    chips = ""
    for a in attendees:
        name = a.get("displayName") or a.get("email","").split("@")[0]
        ok = a.get("responseStatus") == "accepted"
        cls = "ok" if ok else "ng"
        mark = "✓" if ok else ""
        chips += f'<span class="attendee-chip"><span class="dot {cls}"></span>{name} {mark}</span>'
    return chips

def make_card(i, ev, date_key=""):
    color = COLORS[i % len(COLORS)]
    name = ev["summary"].split(" x ")[0].strip()
    avatar = name[0]
    guests = [a for a in ev["attendees"] if a.get("email") != "t.nambara.autotrading@gmail.com"]
    guest_email = guests[0].get("email","") if guests else ""
    msg = ev.get("message","")
    msg_html = f'<div class="card-purpose">{msg}</div>' if msg else '<div class="card-purpose">（メッセージなし）</div>'
    chips = make_chips(ev["attendees"])
    zoom_id = f'ID: {ev["meeting_id"]} ／ PW: {ev["password"]}' if ev.get("meeting_id") else ""

    g = get_gijiroku(date_key, name) if date_key else {"today": None, "past": None, "past_count": 0}
    today_link = g.get("today")
    past_link = g.get("past")
    past_count = g.get("past_count", 0)

    # 未来日付は「今日の議事録」を表示しない
    if date_key:
        try:
            page_date = datetime.date.fromisoformat(date_key)
            if page_date > TODAY:
                today_link = None
        except Exception:
            pass

    if today_link:
        status_badge = '<span class="status-badge recorded">✓ 議事録あり</span>'
        btn_gijiroku = f'<a class="btn-gijiroku" href="{today_link}" target="_blank">📋 本日の議事録</a>'
    else:
        status_badge = '<span class="status-badge pending">録音待ち</span>'
        btn_gijiroku = '<a class="btn-gijiroku-pending">📋 面談後に議事録生成</a>'

    btn_past = f'<a class="btn-past" href="{past_link}" target="_blank">📂 過去の議事録（{past_count}件）</a>' if past_link else ""

    return f"""
    <div class="card" id="meet-{i+1}">
      <div class="card-top">
        <div class="card-avatar" style="background:{color}">{avatar}</div>
        <div class="card-main">
          <div class="card-meta">
            <span class="card-time-badge">{ev["start"]} 〜 {ev["end"]}</span>
            {status_badge}
          </div>
          <div class="card-title">{name}</div>
          <div class="card-company">{guest_email}</div>
          {msg_html}
        </div>
        <div class="card-actions">
          <a class="btn-zoom" href="{ev["zoom_url"]}" target="_blank">▶ Zoom参加</a>
          {btn_gijiroku}
          {btn_past}
        </div>
      </div>
      <div class="card-footer">{chips}<span class="zoom-id-text">{zoom_id}</span></div>
    </div>"""

def make_nav(events):
    items = ""
    for i, ev in enumerate(events):
        name = ev["summary"].split(" x ")[0].strip()
        items += f"""<a class="nav-item" href="#meet-{i+1}" onclick="jump('meet-{i+1}',this)">
        <div class="nav-dot pending"></div>
        <div class="nav-time">{ev["start"]}</div>
        <div class="nav-name">{name}</div></a>"""
    return items

def t2m(t):
    h,m = t.split(":")
    return int(h)*60+int(m)

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans JP',sans-serif;background:#f5f6f8;color:#1a1a2e;min-height:100vh}
header{background:#fff;border-bottom:2px solid #e8eaf0;padding:0 32px;height:56px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.logo-badge{background:#1a73e8;color:#fff;font-size:11px;font-weight:700;padding:3px 9px;border-radius:4px}
.header-title{font-size:15px;font-weight:500;color:#2d2d2d;margin-left:12px}
.header-date{font-size:12px;color:#888}
.back-link{background:#f1f3f4;color:#444;font-size:11px;font-weight:500;padding:5px 12px;border-radius:6px;text-decoration:none;border:1px solid #ddd}
.layout{display:flex;max-width:1200px;margin:0 auto;padding:24px 20px;gap:24px}
.sidebar{width:220px;flex-shrink:0}
.sidebar-card{background:#fff;border-radius:8px;border:1px solid #e8eaf0;padding:16px 0;position:sticky;top:72px}
.sidebar-title{font-size:11px;font-weight:700;color:#888;letter-spacing:.1em;padding:0 16px 12px;text-transform:uppercase}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 16px;cursor:pointer;transition:background .15s;border-left:3px solid transparent;text-decoration:none;color:inherit}
.nav-item:hover{background:#f0f4ff}
.nav-item.active{background:#e8f0fe;border-left-color:#1a73e8}
.nav-time{font-size:11px;color:#1a73e8;font-weight:500;min-width:42px}
.nav-name{font-size:13px;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.nav-dot.pending{background:#dadce0}.nav-dot.now{background:#ea4335;animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.main{flex:1;min-width:0}
.day-banner{background:#fff;border-radius:8px;border:1px solid #e8eaf0;padding:20px 24px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
.day-info h1{font-size:18px;font-weight:700;color:#1a1a2e;margin-bottom:4px}
.day-info p{font-size:12px;color:#777}
.day-stats{display:flex;gap:16px}
.stat{text-align:center}
.stat-num{font-size:22px;font-weight:700;color:#1a73e8;line-height:1}
.stat-label{font-size:10px;color:#888;margin-top:2px}
.card{background:#fff;border-radius:8px;border:1px solid #e8eaf0;margin-bottom:12px;overflow:hidden;transition:box-shadow .2s,border-color .2s;scroll-margin-top:72px}
.card:hover{box-shadow:0 2px 12px rgba(0,0,0,.08);border-color:#c5d0e6}
.card.highlighted{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.15)}
.card-top{display:flex;align-items:flex-start;gap:16px;padding:18px 20px}
.card-avatar{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;font-weight:700;flex-shrink:0}
.card-main{flex:1;min-width:0}
.card-meta{display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap}
.card-time-badge{background:#e8f0fe;color:#1a73e8;font-size:11px;font-weight:700;padding:2px 8px;border-radius:12px}
.status-badge{font-size:10px;padding:2px 8px;border-radius:12px;font-weight:500}
.status-badge.pending{background:#f1f3f4;color:#888}
.card-title{font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:3px}
.card-company{font-size:12px;color:#777;margin-bottom:6px}
.card-purpose{font-size:12px;color:#555;background:#f8f9fc;border-left:3px solid #e0e4ef;padding:6px 10px;border-radius:0 4px 4px 0;line-height:1.6}
.card-actions{display:flex;flex-direction:column;align-items:flex-end;gap:8px;flex-shrink:0;padding-left:8px}
.btn-zoom{display:inline-flex;align-items:center;gap:6px;background:#1a73e8;color:#fff;text-decoration:none;font-size:12px;font-weight:500;padding:7px 14px;border-radius:6px;white-space:nowrap;transition:background .15s}
.btn-zoom:hover{background:#1557b0}
.btn-gijiroku{display:inline-flex;align-items:center;gap:6px;background:#34a853;color:#fff;text-decoration:none;font-size:12px;font-weight:500;padding:7px 14px;border-radius:6px;white-space:nowrap;transition:background .15s}
.btn-gijiroku:hover{background:#1e8e3e}
.btn-gijiroku-pending{display:inline-flex;align-items:center;gap:6px;background:#f1f3f4;color:#888;font-size:12px;font-weight:500;padding:7px 14px;border-radius:6px;white-space:nowrap}
.btn-past{display:inline-flex;align-items:center;gap:6px;background:#fff;color:#5f6368;text-decoration:none;font-size:11px;font-weight:500;padding:5px 12px;border-radius:6px;border:1px solid #dadce0;white-space:nowrap;transition:background .15s}
.btn-past:hover{background:#f1f3f4}
.status-badge.recorded{background:#e6f4ea;color:#188038}
.card-footer{border-top:1px solid #f1f3f4;padding:10px 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.attendee-chip{display:inline-flex;align-items:center;gap:5px;background:#f1f3f4;border-radius:12px;padding:3px 10px;font-size:11px;color:#555}
.attendee-chip .dot{width:5px;height:5px;border-radius:50%}
.attendee-chip .dot.ok{background:#34a853}.attendee-chip .dot.ng{background:#dadce0}
.zoom-id-text{font-size:10px;color:#aaa;margin-left:auto}
@keyframes highlightAnim{0%{border-color:#e8eaf0}40%{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.2)}100%{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.15)}}
.card.pop{animation:highlightAnim .5s ease forwards}
#pw-overlay{position:fixed;inset:0;background:#1a1a2e;display:flex;align-items:center;justify-content:center;z-index:9999}
#pw-box{background:#fff;border-radius:12px;padding:40px 36px;width:320px;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.3)}
#pw-box h2{font-size:16px;font-weight:700;color:#1a1a2e;margin-bottom:6px}
#pw-box p{font-size:12px;color:#888;margin-bottom:20px}
#pw-input{width:100%;border:1.5px solid #e0e4ef;border-radius:8px;padding:10px 14px;font-size:18px;letter-spacing:.3em;text-align:center;outline:none;margin-bottom:12px}
#pw-input:focus{border-color:#1a73e8}
#pw-btn{width:100%;background:#1a73e8;color:#fff;border:none;border-radius:8px;padding:10px;font-size:14px;font-weight:700;cursor:pointer}
#pw-btn:hover{background:#1557b0}
#pw-err{font-size:12px;color:#ea4335;margin-top:8px;display:none}
"""

PW_SCRIPT = """
(function(){
  if(sessionStorage.getItem('bpw')==='ok'){
    document.getElementById('pw-overlay').style.display='none';
  }
})();
function checkPw(){
  if(document.getElementById('pw-input').value==='2467'){
    sessionStorage.setItem('bpw','ok');
    document.getElementById('pw-overlay').style.display='none';
  }else{
    document.getElementById('pw-err').style.display='block';
    document.getElementById('pw-input').value='';
    document.getElementById('pw-input').focus();
  }
}
document.getElementById('pw-input').addEventListener('keydown',function(e){
  if(e.key==='Enter')checkPw();
});
"""

def generate_day(date_key, back=True):
    data = DAYS[date_key]
    label = data["label"]
    events = data["zoom"]
    cards = "".join(make_card(i, ev, date_key) for i, ev in enumerate(events))
    nav = make_nav(events)
    count = len(events)
    sch_js = ",".join(f"{{s:{t2m(ev['start'])},e:{t2m(ev['end'])}}}" for ev in events)
    back_btn = '<a class="back-link" href="index.html">← 日付一覧</a>' if back else ''

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ブリーフィング — {label}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div id="pw-overlay">
  <div id="pw-box">
    <h2>ブリーフィング</h2>
    <p>パスワードを入力してください</p>
    <input id="pw-input" type="password" placeholder="••••" maxlength="20" autofocus>
    <button id="pw-btn" onclick="checkPw()">開く</button>
    <div id="pw-err">パスワードが違います</div>
  </div>
</div>
<script>{PW_SCRIPT}</script>
<header>
  <div style="display:flex;align-items:center">
    <span class="logo-badge">ブリーフィング</span>
    <span class="header-title">南原竜樹 — 本日の面談</span>
  </div>
  <div style="display:flex;align-items:center;gap:12px">
    <div class="header-date">{label}</div>
    {back_btn}
    <a href="https://editor.shabelab.com/login.html" target="_blank" class="back-link">いきなり議事録</a>
  </div>
</header>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-card">
      <div class="sidebar-title">タイムライン</div>
      {nav}
    </div>
  </aside>
  <main class="main">
    <div class="day-banner">
      <div class="day-info">
        <h1>{label}</h1>
        <p>本日のZoom面談スケジュール</p>
      </div>
      <div class="day-stats">
        <div class="stat"><div class="stat-num">{count}</div><div class="stat-label">Zoom面談</div></div>
        <div class="stat"><div class="stat-num" style="color:#888">{count}</div><div class="stat-label">録音待ち</div></div>
      </div>
    </div>
    {cards if cards else '<div style="background:#fff;border-radius:8px;border:1px solid #e8eaf0;padding:60px 24px;text-align:center;color:#aaa"><div style="font-size:32px">📅</div><p style="font-size:14px;margin-top:8px">本日のZoom面談はありません</p></div>'}
  </main>
</div>
<script>
function jump(id,el){{
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  if(el)el.classList.add('active');
  const card=document.getElementById(id);
  if(!card)return;
  card.scrollIntoView({{behavior:'smooth',block:'start'}});
  document.querySelectorAll('.card').forEach(c=>c.classList.remove('highlighted','pop'));
  setTimeout(()=>{{card.classList.add('highlighted','pop')}},300);
}}
(function(){{
  const now=new Date();
  const m=now.getHours()*60+now.getMinutes();
  const sch=[{sch_js}];
  document.querySelectorAll('.nav-item').forEach((el,i)=>{{
    if(!sch[i])return;
    if(m>=sch[i].s&&m<sch[i].e){{
      el.classList.add('active');
      el.querySelector('.nav-dot').className='nav-dot now';
      document.getElementById('meet-'+(i+1))?.classList.add('highlighted');
    }}
  }});
}})();
</script>
</body>
</html>"""

# index.html（日付一覧）
def generate_index():
    cards = ""
    for date_key, data in sorted(DAYS.items(), reverse=True):
        label = data["label"]
        events = data["zoom"]
        count = len(events)
        try:
            page_date = datetime.date.fromisoformat(date_key)
            is_today = page_date == TODAY
            is_future = page_date > TODAY
        except Exception:
            is_today = is_future = False

        today_badge = '<span class="today-badge">今日</span>' if is_today else ""
        future_badge = '<span class="future-badge">予定</span>' if is_future else ""

        if count == 0:
            schedule_html = '<div class="day-card-no-meetings">面談なし</div>'
        else:
            items = "".join(
                f'<span class="sch-item"><span class="sch-time">{ev["start"]}</span><span class="sch-name">{ev["summary"].split(" x ")[0].strip()}</span></span>'
                for ev in events
            )
            schedule_html = f'<div class="day-card-schedule">{items}</div>'

        cards += f"""
        <a class="day-card{'  day-today' if is_today else ''}" href="{date_key}.html">
          <div class="day-card-body">
            <div class="day-card-header">
              <span class="day-card-date">{label}</span>
              {today_badge}{future_badge}
              <span class="day-card-count">Zoom面談 {count}件</span>
            </div>
            {schedule_html}
          </div>
          <div class="day-card-arrow">→</div>
        </a>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ブリーフィング 日付一覧</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Noto Sans JP',sans-serif;background:#f5f6f8;color:#1a1a2e;min-height:100vh}}
header{{background:#fff;border-bottom:2px solid #e8eaf0;padding:0 32px;height:56px;display:flex;align-items:center;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.logo-badge{{background:#1a73e8;color:#fff;font-size:11px;font-weight:700;padding:3px 9px;border-radius:4px}}
.header-title{{font-size:15px;font-weight:500;color:#2d2d2d;margin-left:12px}}
.wrap{{max-width:640px;margin:40px auto;padding:0 20px}}
h1{{font-size:16px;font-weight:700;color:#555;margin-bottom:16px}}
.day-card{{display:flex;align-items:center;gap:16px;background:#fff;border:1px solid #e8eaf0;border-radius:8px;padding:16px 20px;margin-bottom:10px;text-decoration:none;color:inherit;transition:box-shadow .15s,border-color .15s}}
.day-card:hover{{box-shadow:0 2px 12px rgba(0,0,0,.08);border-color:#c5d0e6}}
.day-today{{border-left:4px solid #1a73e8;background:#f0f4ff}}
.day-card-body{{flex:1;min-width:0}}
.day-card-header{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px}}
.day-card-date{{font-size:15px;font-weight:700;color:#1a1a2e}}
.day-card-count{{font-size:12px;color:#888;margin-left:auto}}
.today-badge{{background:#1a73e8;color:#fff;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px}}
.future-badge{{background:#f0f4ff;color:#1a73e8;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;border:1px solid #c5d0e6}}
.day-card-schedule{{display:flex;flex-wrap:wrap;gap:6px}}
.sch-item{{display:flex;align-items:center;gap:4px;background:#f5f6f8;border-radius:4px;padding:3px 8px}}
.sch-time{{font-size:11px;color:#1a73e8;font-weight:700;min-width:36px}}
.sch-name{{font-size:12px;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px}}
.day-card-no-meetings{{font-size:12px;color:#bbb}}
.day-card-arrow{{font-size:16px;color:#1a73e8;flex-shrink:0}}
#pw-overlay{{position:fixed;inset:0;background:#1a1a2e;display:flex;align-items:center;justify-content:center;z-index:9999}}
#pw-box{{background:#fff;border-radius:12px;padding:40px 36px;width:320px;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,.3)}}
#pw-box h2{{font-size:16px;font-weight:700;color:#1a1a2e;margin-bottom:6px}}
#pw-box p{{font-size:12px;color:#888;margin-bottom:20px}}
#pw-input{{width:100%;border:1.5px solid #e0e4ef;border-radius:8px;padding:10px 14px;font-size:18px;letter-spacing:.3em;text-align:center;outline:none;margin-bottom:12px}}
#pw-input:focus{{border-color:#1a73e8}}
#pw-btn{{width:100%;background:#1a73e8;color:#fff;border:none;border-radius:8px;padding:10px;font-size:14px;font-weight:700;cursor:pointer}}
#pw-btn:hover{{background:#1557b0}}
#pw-err{{font-size:12px;color:#ea4335;margin-top:8px;display:none}}
</style>
</head>
<body>
<div id="pw-overlay">
  <div id="pw-box">
    <h2>ブリーフィング</h2>
    <p>パスワードを入力してください</p>
    <input id="pw-input" type="password" placeholder="••••" maxlength="20" autofocus>
    <button id="pw-btn" onclick="checkPw()">開く</button>
    <div id="pw-err">パスワードが違います</div>
  </div>
</div>
<script>{PW_SCRIPT}</script>
<header>
  <span class="logo-badge">ブリーフィング</span>
  <span class="header-title">南原竜樹 — 面談一覧</span>
</header>
<div class="wrap">
  <h1>日付を選択</h1>
  {cards}
</div>
</body>
</html>"""

for date_key in DAYS:
    html = generate_day(date_key)
    with open(f"{date_key}.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{date_key}.html OK")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(generate_index())
print("index.html OK")
