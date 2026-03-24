"""
毎朝自動でブリーフィングページを生成するスクリプト
"""
import os, json, datetime, re
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from playwright.sync_api import sync_playwright
import time

JST = ZoneInfo("Asia/Tokyo")
TODAY = datetime.date.today()
TODAY_STR = f"{TODAY.year}年{TODAY.month}月{TODAY.day}日"
WEEKDAY = ["月","火","水","木","金","土","日"][TODAY.weekday()]

# ── Google Calendar ──────────────────────────────────────────
def get_calendar_events():
    creds_json = os.environ.get("GOOGLE_TOKEN")
    client_json = os.environ.get("GOOGLE_CLIENT")

    creds = Credentials.from_authorized_user_info(
        json.loads(creds_json),
        scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build("calendar", "v3", credentials=creds)

    time_min = datetime.datetime.combine(TODAY, datetime.time.min, tzinfo=JST).isoformat()
    time_max = datetime.datetime.combine(TODAY, datetime.time.max, tzinfo=JST).isoformat()

    calendar_id = os.environ.get("CALENDAR_ID", "t.nambara.autotrading@gmail.com")

    result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = result.get("items", [])
    zoom_meetings = []

    for ev in events:
        desc = ev.get("description", "")
        if "zoom.us" not in desc.lower():
            continue

        # Zoom URL抽出
        zoom_url = re.search(r'https://[^\s<"]+zoom\.us/j/[^\s<"]+', desc)
        meeting_id = re.search(r'ミーティングID[：:]\s*([\d\s]+)', desc)
        password = re.search(r'パスワード[：:]\s*(\S+)', desc)

        attendees = ev.get("attendees", [])
        guests = [a for a in attendees if not a.get("self")]

        start = ev.get("start", {}).get("dateTime", "")
        end   = ev.get("end",   {}).get("dateTime", "")

        start_dt = datetime.datetime.fromisoformat(start).astimezone(JST) if start else None
        end_dt   = datetime.datetime.fromisoformat(end).astimezone(JST)   if end   else None

        # 参加者メッセージ抽出
        msg_match = re.search(r'主催者へのメッセージ[：:]\s*(.+?)(?:\n|<)', desc, re.DOTALL)
        message = msg_match.group(1).strip() if msg_match else ""

        zoom_meetings.append({
            "title":      ev.get("summary", ""),
            "start":      start_dt.strftime("%H:%M") if start_dt else "",
            "end":        end_dt.strftime("%H:%M")   if end_dt   else "",
            "zoom_url":   zoom_url.group(0) if zoom_url else "",
            "meeting_id": meeting_id.group(1).strip() if meeting_id else "",
            "password":   password.group(1).strip() if password else "",
            "attendees":  attendees,
            "guests":     guests,
            "message":    message,
        })

    return zoom_meetings


# ── いきなり議事録 ────────────────────────────────────────────
def get_gijiroku_links(meetings):
    email    = os.environ.get("GIJIROKU_EMAIL")
    password = os.environ.get("GIJIROKU_PASSWORD")

    if not email or not password:
        return {i: {"today": None, "past": None, "past_count": 0} for i in range(len(meetings))}

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        page.goto("https://editor.shabelab.com/login.html")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        page.fill('input[type="email"]', email)
        page.fill('input[type="password"]', password)
        page.get_by_text("ログイン", exact=True).last.click()
        try:
            page.wait_for_url(lambda url: "login" not in url, timeout=8000)
        except:
            pass
        time.sleep(2)

        today_str = TODAY.strftime("%Y/%m/%d")

        def search_links(keyword):
            page.goto("https://editor.shabelab.com/narancia_top.html?folder=team")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            page.locator("text=キーワード").first.click()
            time.sleep(0.5)
            try:
                inp = page.locator('input[type="text"], input:not([type])').first
                inp.fill(keyword)
                page.keyboard.press("Enter")
                time.sleep(0.5)
            except:
                pass
            page.locator("text=検索").first.click()
            time.sleep(2)
            return page.eval_on_selector_all(
                'a[href*="gijiroku_detail"]',
                'els => els.map(e => e.href)'
            )

        for i, meeting in enumerate(meetings):

            name_match = re.match(r'^([^xX×]+?)\s*[xX×]', meeting["title"])
            name = name_match.group(1).strip() if name_match else ""
            if not name:
                results[i] = {"today": None, "past": None, "past_count": 0}
                continue

            # 今日の議事録：日付+名前で検索
            today_links = search_links(f"{name[:4]} {today_str}")
            today_link  = today_links[0] if today_links else None

            # 全件：名前のみで検索
            all_links  = search_links(name[:4])
            past_links = [l for l in all_links if l != today_link]
            past_link  = past_links[0] if past_links else None
            past_count = len(past_links)

            results[i] = {
                "today":      today_link,
                "past":       past_link,
                "past_count": past_count,
            }
            print(f"  {name}: today={today_link is not None}, past={past_count}件")

        browser.close()
    return results


# ── HTML生成 ──────────────────────────────────────────────────
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

def make_attendee_chips(attendees):
    chips = ""
    for a in attendees:
        name  = a.get("displayName") or a.get("email","").split("@")[0]
        ok    = a.get("responseStatus") == "accepted"
        cls   = "ok" if ok else "ng"
        mark  = "✓" if ok else ""
        chips += f'<span class="attendee-chip"><span class="dot {cls}"></span>{name} {mark}</span>'
    return chips

def make_card(i, meeting, links):
    idx    = i % len(COLORS)
    color  = COLORS[idx]
    name   = meeting["title"].split(" x ")[0].split("×")[0].strip()
    avatar = name[0] if name else "？"
    guest  = meeting["guests"][0] if meeting["guests"] else None
    guest_email = guest.get("email", "") if guest else ""

    today_link = links.get("today")
    past_link  = links.get("past")
    past_count = links.get("past_count", 0)

    btn_today = (
        f'<a class="btn-gijiroku" href="{today_link}" target="_blank">📋 本日の議事録</a>'
        if today_link else
        '<a class="btn-gijiroku-pending">📋 面談後に議事録生成</a>'
    )
    btn_past = (
        f'<a class="btn-past" href="{past_link}" target="_blank">📂 過去の議事録（{past_count}件）</a>'
        if past_link else ""
    )

    msg = meeting["message"]
    msg_html = f'<div class="card-purpose">{msg}</div>' if msg else '<div class="card-purpose">（メッセージなし）</div>'

    chips = make_attendee_chips(meeting["attendees"])
    zoom_id_text = f'ID: {meeting["meeting_id"]} ／ PW: {meeting["password"]}' if meeting["meeting_id"] else ""

    return f"""
    <div class="card" id="meet-{i+1}">
      <div class="card-top">
        <div class="card-avatar" style="background:{color}">{avatar}</div>
        <div class="card-main">
          <div class="card-meta">
            <span class="card-time-badge">{meeting["start"]} 〜 {meeting["end"]}</span>
            <span class="status-badge {'recorded' if today_link else 'pending'}">
              {'✓ 議事録あり' if today_link else '録音待ち'}
            </span>
          </div>
          <div class="card-title">{name}</div>
          <div class="card-company">{guest_email}</div>
          {msg_html}
        </div>
        <div class="card-actions">
          <a class="btn-zoom" href="{meeting["zoom_url"]}" target="_blank">▶ Zoom参加</a>
          {btn_today}
          {btn_past}
        </div>
      </div>
      <div class="card-footer">
        {chips}
        <span class="zoom-id-text">{zoom_id_text}</span>
      </div>
    </div>"""


def make_nav_items(meetings, gijiroku):
    items = ""
    for i, m in enumerate(meetings):
        name = m["title"].split(" x ")[0].split("×")[0].strip()
        dot_cls = "recorded" if gijiroku.get(i, {}).get("today") else "pending"
        items += f"""
      <a class="nav-item" href="#meet-{i+1}" onclick="jump('meet-{i+1}',this)">
        <div class="nav-dot {dot_cls}"></div>
        <div class="nav-time">{m["start"]}</div>
        <div class="nav-name">{name}</div>
      </a>"""
    return items


def _time_to_min(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)

def generate_html(meetings, gijiroku):
    cards    = "".join(make_card(i, m, gijiroku.get(i, {})) for i, m in enumerate(meetings))
    nav      = make_nav_items(meetings, gijiroku)
    count    = len(meetings)
    recorded = sum(1 for v in gijiroku.values() if v.get("today"))
    schedule_js = ",".join(
        f"{{s:{_time_to_min(m['start'])},e:{_time_to_min(m['end'])}}}"
        for m in meetings if m.get("start") and m.get("end")
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ブリーフィング — {TODAY_STR}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Noto Sans JP',sans-serif;background:#f5f6f8;color:#1a1a2e;min-height:100vh}}
header{{background:#fff;border-bottom:2px solid #e8eaf0;padding:0 32px;height:56px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.logo-badge{{background:#1a73e8;color:#fff;font-size:11px;font-weight:700;padding:3px 9px;border-radius:4px}}
.header-title{{font-size:15px;font-weight:500;color:#2d2d2d;margin-left:12px}}
.header-date{{font-size:12px;color:#888}}
.layout{{display:flex;max-width:1200px;margin:0 auto;padding:24px 20px;gap:24px}}
.sidebar{{width:220px;flex-shrink:0}}
.sidebar-card{{background:#fff;border-radius:8px;border:1px solid #e8eaf0;padding:16px 0;position:sticky;top:72px}}
.sidebar-title{{font-size:11px;font-weight:700;color:#888;letter-spacing:.1em;padding:0 16px 12px;text-transform:uppercase}}
.nav-item{{display:flex;align-items:center;gap:10px;padding:9px 16px;cursor:pointer;transition:background .15s;border-left:3px solid transparent;text-decoration:none;color:inherit}}
.nav-item:hover{{background:#f0f4ff}}
.nav-item.active{{background:#e8f0fe;border-left-color:#1a73e8}}
.nav-time{{font-size:11px;color:#1a73e8;font-weight:500;min-width:42px}}
.nav-name{{font-size:13px;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.nav-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
.nav-dot.recorded{{background:#34a853}}.nav-dot.pending{{background:#dadce0}}.nav-dot.now{{background:#ea4335;animation:blink 1.5s infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.sidebar-divider{{margin:8px 16px;border:none;border-top:1px solid #e8eaf0}}
.nav-nonmeeting{{padding:7px 16px;font-size:11px;color:#aaa}}
.main{{flex:1;min-width:0}}
.day-banner{{background:#fff;border-radius:8px;border:1px solid #e8eaf0;padding:20px 24px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}}
.day-info h1{{font-size:18px;font-weight:700;color:#1a1a2e;margin-bottom:4px}}
.day-info p{{font-size:12px;color:#777}}
.day-stats{{display:flex;gap:16px}}
.stat{{text-align:center}}
.stat-num{{font-size:22px;font-weight:700;color:#1a73e8;line-height:1}}
.stat-label{{font-size:10px;color:#888;margin-top:2px}}
.card{{background:#fff;border-radius:8px;border:1px solid #e8eaf0;margin-bottom:12px;overflow:hidden;transition:box-shadow .2s,border-color .2s;scroll-margin-top:72px}}
.card:hover{{box-shadow:0 2px 12px rgba(0,0,0,.08);border-color:#c5d0e6}}
.card.highlighted{{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.15),0 4px 16px rgba(26,115,232,.1)}}
.card-top{{display:flex;align-items:flex-start;gap:16px;padding:18px 20px}}
.card-avatar{{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;font-weight:700;flex-shrink:0}}
.card-main{{flex:1;min-width:0}}
.card-meta{{display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap}}
.card-time-badge{{background:#e8f0fe;color:#1a73e8;font-size:11px;font-weight:700;padding:2px 8px;border-radius:12px}}
.status-badge{{font-size:10px;padding:2px 8px;border-radius:12px;font-weight:500}}
.status-badge.recorded{{background:#e6f4ea;color:#188038}}
.status-badge.pending{{background:#f1f3f4;color:#888}}
.card-title{{font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:3px}}
.card-company{{font-size:12px;color:#777;margin-bottom:6px}}
.card-purpose{{font-size:12px;color:#555;background:#f8f9fc;border-left:3px solid #e0e4ef;padding:6px 10px;border-radius:0 4px 4px 0;line-height:1.6}}
.card-actions{{display:flex;flex-direction:column;align-items:flex-end;gap:8px;flex-shrink:0;padding-left:8px}}
.btn-zoom{{display:inline-flex;align-items:center;gap:6px;background:#1a73e8;color:#fff;text-decoration:none;font-size:12px;font-weight:500;padding:7px 14px;border-radius:6px;white-space:nowrap;transition:background .15s}}
.btn-zoom:hover{{background:#1557b0}}
.btn-gijiroku{{display:inline-flex;align-items:center;gap:6px;background:#34a853;color:#fff;text-decoration:none;font-size:12px;font-weight:500;padding:7px 14px;border-radius:6px;white-space:nowrap;transition:background .15s}}
.btn-gijiroku:hover{{background:#1e8e3e}}
.btn-gijiroku-pending{{display:inline-flex;align-items:center;gap:6px;background:#f1f3f4;color:#888;font-size:12px;font-weight:500;padding:7px 14px;border-radius:6px;white-space:nowrap}}
.btn-past{{display:inline-flex;align-items:center;gap:6px;background:#fff;color:#5f6368;text-decoration:none;font-size:11px;font-weight:500;padding:5px 12px;border-radius:6px;border:1px solid #dadce0;white-space:nowrap;transition:background .15s}}
.btn-past:hover{{background:#f1f3f4}}
.card-footer{{border-top:1px solid #f1f3f4;padding:10px 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
.attendee-chip{{display:inline-flex;align-items:center;gap:5px;background:#f1f3f4;border-radius:12px;padding:3px 10px;font-size:11px;color:#555}}
.attendee-chip .dot{{width:5px;height:5px;border-radius:50%}}
.attendee-chip .dot.ok{{background:#34a853}}.attendee-chip .dot.ng{{background:#dadce0}}
.zoom-id-text{{font-size:10px;color:#aaa;margin-left:auto}}
@keyframes highlightAnim{{0%{{border-color:#e8eaf0;box-shadow:none}}40%{{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.2)}}100%{{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.15)}}}}
.card.pop{{animation:highlightAnim .5s ease forwards}}
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
<script>
(function(){{
  if(sessionStorage.getItem('bpw')==='ok'){{
    document.getElementById('pw-overlay').style.display='none';
  }}
}})();
function checkPw(){{
  if(document.getElementById('pw-input').value==='2467'){{
    sessionStorage.setItem('bpw','ok');
    document.getElementById('pw-overlay').style.display='none';
  }}else{{
    document.getElementById('pw-err').style.display='block';
    document.getElementById('pw-input').value='';
    document.getElementById('pw-input').focus();
  }}
}}
document.getElementById('pw-input').addEventListener('keydown',function(e){{
  if(e.key==='Enter')checkPw();
}});
</script>
<header>
  <div style="display:flex;align-items:center">
    <span class="logo-badge">ブリーフィング</span>
    <span class="header-title">南原竜樹 — 本日の面談</span>
  </div>
  <div style="display:flex;align-items:center;gap:12px">
    <div class="header-date">{TODAY_STR}（{WEEKDAY}）</div>
    <a href="https://editor.shabelab.com/login.html" target="_blank"
       style="background:#f1f3f4;color:#444;font-size:11px;font-weight:500;padding:5px 12px;border-radius:6px;text-decoration:none;border:1px solid #ddd">
      いきなり議事録 ログイン
    </a>
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
        <h1>{TODAY_STR}（{WEEKDAY}）</h1>
        <p>本日のZoom面談スケジュール</p>
      </div>
      <div class="day-stats">
        <div class="stat"><div class="stat-num">{count}</div><div class="stat-label">Zoom面談</div></div>
        <div class="stat"><div class="stat-num" style="color:#34a853">{recorded}</div><div class="stat-label">議事録あり</div></div>
        <div class="stat"><div class="stat-num" style="color:#888">{count-recorded}</div><div class="stat-label">録音待ち</div></div>
      </div>
    </div>
    {cards}
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
  const sch=[{schedule_js}];
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


if __name__ == "__main__":
    print(f"📅 {TODAY_STR} のブリーフィングを生成中...")
    try:
        print("1. Googleカレンダーを取得中...")
        meetings = get_calendar_events()
        print(f"   Zoom面談 {len(meetings)}件 取得")

        print("2. いきなり議事録を検索中...")
        gijiroku = get_gijiroku_links(meetings)

        print("3. HTML生成中...")
        html = generate_html(meetings, gijiroku)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("✅ index.html 生成完了")

    except Exception as e:
        print(f"❌ エラー: {e}")
        error_html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<title>エラー</title>
<style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f5f6f8}}
.box{{background:#fff;border-radius:12px;padding:40px;text-align:center;border:1px solid #e8eaf0;max-width:400px}}
h1{{color:#ea4335;font-size:18px;margin-bottom:12px}}p{{color:#555;font-size:13px;line-height:1.6}}</style>
</head><body><div class="box">
<h1>⚠️ 生成エラー</h1>
<p>{TODAY_STR}（{WEEKDAY}）のブリーフィング生成に失敗しました。</p>
<p style="margin-top:12px;color:#aaa;font-size:11px">{e}</p>
</div></body></html>"""
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(error_html)
        raise
