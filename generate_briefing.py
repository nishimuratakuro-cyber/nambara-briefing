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
def get_calendar_events(target_date=None):
    if target_date is None:
        target_date = TODAY
    creds_json = os.environ.get("GOOGLE_TOKEN")
    client_json = os.environ.get("GOOGLE_CLIENT")

    creds = Credentials.from_authorized_user_info(
        json.loads(creds_json),
        scopes=["https://www.googleapis.com/auth/calendar.readonly"]
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build("calendar", "v3", credentials=creds)

    time_min = datetime.datetime.combine(target_date, datetime.time.min, tzinfo=JST).isoformat()
    time_max = datetime.datetime.combine(target_date, datetime.time.max, tzinfo=JST).isoformat()

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
        password = re.search(r'パスワード[：:]\s*([^\s<]+)', desc)

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


# ── 名前から検索キーを抽出（いきなり議事録・Lステップ共用）────────────
def extract_search_key(n):
    # 絵文字・記号を除去
    s = re.sub(r'[^\w\s\u3000-\u9fff\u30a0-\u30ff\u3040-\u309f]', '', n).strip()
    s = re.sub(r'^(株式会社|有限会社|合同会社|一般社団法人|公益社団法人)\s*', '', s).strip()
    s = s.replace('\u3000', ' ')
    if re.match(r'^[A-Za-z\s]+$', s):
        words = s.split()
        return words[-1] if words else n[:4]
    if re.match(r'^[A-Za-z0-9]', s):
        j = re.sub(r'^[A-Za-z0-9]+\s*', '', s).strip()
        if j:
            return j[:4]
    if ' ' in s:
        before, after = s.rsplit(' ', 1)
        if len(before) > 4:
            return before[-2:]
        else:
            return after[:4]
    return s[:4]


# ── いきなり議事録 ────────────────────────────────────────────
def get_all_gijiroku_links(meetings_by_date):
    """
    meetings_by_date: {date: [meeting, ...]}
    ブラウザを1回だけ起動し、名前ごとに1回だけ検索して全日付分の議事録リンクを返す。
    returns: {date: {index: {today, past, past_count}}}
    """
    email    = os.environ.get("GIJIROKU_EMAIL")
    password = os.environ.get("GIJIROKU_PASSWORD")

    empty = lambda meetings: {i: {"today": None, "past": None, "past_count": 0} for i in range(len(meetings))}
    if not email or not password:
        return {d: empty(m) for d, m in meetings_by_date.items()}

    # 全日付から名前一覧を収集（重複除去）
    name_cache = {}  # name_key -> all_links（名前のみ検索、キャッシュ）

    results = {d: {} for d in meetings_by_date}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
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

        for target_date, meetings in meetings_by_date.items():
            is_today = (target_date == TODAY)
            for i, meeting in enumerate(meetings):
                name = meeting["title"].split(" x ")[0].split("×")[0].strip()
                if not name:
                    results[target_date][i] = {"today": None, "past": None, "past_count": 0}
                    continue

                name_key = name  # キャッシュキーは衝突防止のためフルネーム
                search_keyword = extract_search_key(name)

                # 名前ごとに1回だけ全件検索（キャッシュ済みならスキップ）
                if name_key not in name_cache:
                    all_links = search_links(search_keyword)
                    name_cache[name_key] = all_links
                    print(f"  検索: {name} ({search_keyword}) → {len(all_links)}件")
                else:
                    all_links = name_cache[name_key]

                # 今日の議事録：面談開始済み＆議事録あり → all_links[0]が最新（今日）
                # いきなり議事録は日付+名前の複合検索に非対応のため名前のみ検索
                if is_today:
                    now_min = datetime.datetime.now(JST).hour * 60 + datetime.datetime.now(JST).minute
                    start_str = meeting.get("start", "")
                    if start_str:
                        sh, sm = map(int, start_str.split(":"))
                        started = now_min >= sh * 60 + sm
                    else:
                        started = False
                    today_link = all_links[0] if (started and all_links) else None
                    print(f"  今日: {name} 開始{start_str} 経過={started} リンク={'あり' if today_link else 'なし'}")
                    past_links = all_links[1:] if today_link else all_links
                else:
                    today_link = None  # 未来は今日の議事録なし
                    past_links = all_links

                past_link  = past_links[0] if past_links else None
                past_count = len(past_links)

                results[target_date][i] = {
                    "today":      today_link,
                    "past":       past_link,
                    "past_count": past_count,
                }

        browser.close()
    return results


# ── Lステップ ─────────────────────────────────────────────────
def get_lstep_links(meetings_by_date):
    """
    Lステップの友だちリストから各参加者のプロフィールリンクを取得する。
    returns: {date: {index: url_or_none}}
    """
    email    = os.environ.get("LSTEP_EMAIL")
    password = os.environ.get("LSTEP_PASSWORD")

    empty = lambda meetings: {i: None for i in range(len(meetings))}
    if not email or not password:
        return {d: empty(m) for d, m in meetings_by_date.items()}

    results = {d: empty(meetings_by_date[d]) for d in meetings_by_date}
    name_cache = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # ログイン（LステップはIDがメールアドレスでない場合あり）
        page.goto("https://manager.linestep.net/account/login", timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        # ログインIDフィールド（email型・text型どちらにも対応）
        id_input = page.locator('input[type="email"], input[name="email"], input[name="login_id"], input[type="text"]').first
        id_input.fill(email)
        page.fill('input[type="password"]', password)
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        try:
            page.wait_for_url(lambda url: "login" not in url, timeout=15000)
        except Exception:
            print("⚠️ Lステップ: ログインに失敗しました（LSTEP_EMAIL/PASSWORDを確認してください）")
            browser.close()
            return results
        time.sleep(2)

        def search_friend(keyword):
            page.goto("https://manager.linestep.net/line/friends")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            try:
                page.fill('input[placeholder="友だち名検索"]', keyword)
                page.locator("text=検索").first.click()
                time.sleep(2)
            except:
                pass
            links = page.eval_on_selector_all(
                'a[href*="/line/detail/"]',
                'els => els.map(e => e.href)'
            )
            return links[0] if links else None

        for target_date, meetings in meetings_by_date.items():
            for i, meeting in enumerate(meetings):
                name = meeting["title"].split(" x ")[0].split("×")[0].strip()
                if not name:
                    continue
                search_keyword = extract_search_key(name)
                if name not in name_cache:
                    link = search_friend(search_keyword)
                    name_cache[name] = link
                    print(f"  Lステップ: {name} ({search_keyword}) → {'あり' if link else 'なし'}")
                results[target_date][i] = name_cache[name]

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

def make_card(i, meeting, links, lstep_link=None):
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
    btn_lstep = (
        f'<a class="btn-lstep" href="{lstep_link}" target="_blank">💬 Lステップ</a>'
        if lstep_link else ""
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
          <div class="card-title">{f'<a href="{today_link}" target="_blank" class="card-title-link">{name}</a>' if today_link else name}</div>
          <div class="card-company">{guest_email}</div>
          {msg_html}
        </div>
        <div class="card-actions">
          <a class="btn-zoom" href="{meeting["zoom_url"]}" target="_blank">▶ Zoom参加</a>
          {btn_today}
          {btn_past}
          {btn_lstep}
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

def generate_html(meetings, gijiroku, lstep=None, target_date=None):
    if target_date is None:
        target_date = TODAY
    date_str = f"{target_date.year}年{target_date.month}月{target_date.day}日"
    weekday  = ["月","火","水","木","金","土","日"][target_date.weekday()]
    cards    = "".join(make_card(i, m, gijiroku.get(i, {}), (lstep or {}).get(i)) for i, m in enumerate(meetings))
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
<title>ブリーフィング — {date_str}</title>
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
.card-title{{font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:3px}}.card-title-link{{color:#1a73e8;text-decoration:none;border-bottom:1px solid #c5d0e6}}.card-title-link:hover{{border-bottom-color:#1a73e8}}
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
.btn-lstep{{display:inline-flex;align-items:center;gap:6px;background:#06c755;color:#fff;text-decoration:none;font-size:12px;font-weight:500;padding:7px 14px;border-radius:6px;white-space:nowrap;transition:background .15s}}
.btn-lstep:hover{{background:#05a847}}
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
    <div class="header-date">{date_str}（{weekday}）</div>
    <a href="index.html" style="background:#f1f3f4;color:#444;font-size:11px;font-weight:500;padding:5px 12px;border-radius:6px;text-decoration:none;border:1px solid #ddd">← 日付一覧</a>
    <a href="https://editor.shabelab.com/login.html" target="_blank" style="background:#f1f3f4;color:#444;font-size:11px;font-weight:500;padding:5px 12px;border-radius:6px;text-decoration:none;border:1px solid #ddd">いきなり議事録 ログイン</a>
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
        <h1>{date_str}（{weekday}）</h1>
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


PW_SCRIPT = """
(function(){
  var d=localStorage.getItem('bpw_exp');
  if(d&&Date.now()<parseInt(d)){
    document.getElementById('pw-overlay').style.display='none';
  }
})();
function checkPw(){
  if(document.getElementById('pw-input').value==='2467'){
    localStorage.setItem('bpw_exp',Date.now()+86400000);
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


def regenerate_index(meetings_by_date=None):
    import glob as _glob
    all_files = _glob.glob("20??-??-??.html")
    today_str = TODAY.isoformat()
    future = sorted([f for f in all_files if f.replace(".html","") > today_str])
    past   = sorted([f for f in all_files if f.replace(".html","") < today_str], reverse=True)
    today_file = [f for f in all_files if f.replace(".html","") == today_str]
    files = today_file + future + past
    cards = ""
    past_cards = ""
    for fname in files:
        date_key = fname.replace(".html", "")
        try:
            page_date = datetime.date.fromisoformat(date_key)
            y, m, d = date_key.split("-")
            weekday = ["月","火","水","木","金","土","日"][page_date.weekday()]
            label = f"{y}年{int(m)}月{int(d)}日（{weekday}）"
            is_today  = page_date == TODAY
            is_future = page_date > TODAY
        except Exception:
            label = date_key
            is_today = is_future = False

        today_badge  = '<span class="today-badge">今日</span>' if is_today else ""
        future_badge = '<span class="future-badge">予定</span>' if is_future else ""

        # スケジュール情報（今日・未来はmeetings_by_dateから、過去はHTMLから読み取る）
        events = (meetings_by_date or {}).get(page_date, [])
        count = len(events)
        if count > 0:
            items = "".join(
                f'<span class="sch-item"><span class="sch-time">{ev["start"]}</span>'
                f'<span class="sch-name">{ev["title"].split(" x ")[0].split("×")[0].strip()}</span></span>'
                for ev in events
            )
            schedule_html = f'<div class="day-card-schedule">{items}</div>'
        elif page_date < TODAY:
            # 過去日付: HTMLファイルのサイドバーから件数・スケジュールを復元
            try:
                with open(fname, encoding="utf-8") as fp:
                    fh = fp.read()
                nav_times = re.findall(r'<div class="nav-time">([^<]+)</div>', fh)
                nav_names = re.findall(r'<div class="nav-name">([^<]+)</div>', fh)
                count = len(nav_times)
                if count > 0:
                    items = "".join(
                        f'<span class="sch-item"><span class="sch-time">{t}</span>'
                        f'<span class="sch-name">{n}</span></span>'
                        for t, n in zip(nav_times, nav_names)
                    )
                    schedule_html = f'<div class="day-card-schedule">{items}</div>'
                else:
                    schedule_html = '<div class="day-card-no-meetings">面談なし</div>'
            except Exception:
                schedule_html = '<div class="day-card-no-meetings">面談なし</div>'
        else:
            schedule_html = '<div class="day-card-no-meetings">面談なし</div>'

        card_html = f"""
        <a class="day-card{'  day-today' if is_today else ''}" href="{fname}">
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
        if page_date < TODAY:
            past_cards += card_html
        else:
            cards += card_html

    html = f"""<!DOCTYPE html>
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
.past-section{{margin-top:24px}}
.past-toggle{{display:flex;align-items:center;gap:8px;background:none;border:none;cursor:pointer;padding:10px 0;font-family:inherit;font-size:13px;color:#888;font-weight:500}}
.past-toggle:hover{{color:#555}}
.past-toggle-icon{{font-size:12px;transition:transform .2s}}
.past-toggle.open .past-toggle-icon{{transform:rotate(90deg)}}
.past-cards{{display:none}}
.past-cards.open{{display:block}}
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
  {f'''<div class="past-section">
    <button class="past-toggle" onclick="this.classList.toggle('open');document.getElementById('past-cards').classList.toggle('open')">
      <span class="past-toggle-icon">▶</span> 過去の記録（{past_cards.count('<a class="day-card')}件）
    </button>
    <div class="past-cards" id="past-cards">{past_cards}</div>
  </div>''' if past_cards else ''}
</div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html 再生成完了")


if __name__ == "__main__":
    GENERATE_DAYS = 7

    # 1. 全日付のカレンダーイベントを取得
    print("1. Googleカレンダーを取得中...")
    meetings_by_date = {}
    for offset in range(GENERATE_DAYS):
        target = TODAY + datetime.timedelta(days=offset)
        if target.weekday() >= 5:  # 土日はスキップ
            print(f"   {target}: 土日のためスキップ")
            continue
        try:
            meetings_by_date[target] = get_calendar_events(target)
            print(f"   {target}: {len(meetings_by_date[target])}件")
        except Exception as e:
            print(f"   {target}: 取得失敗 ({e})")
            meetings_by_date[target] = []

    # 2. いきなり議事録を全日付まとめて取得（ブラウザ1回・名前重複なし）
    print("\n2. いきなり議事録を検索中...")
    try:
        all_gijiroku = get_all_gijiroku_links(meetings_by_date)
    except Exception as e:
        print(f"⚠️ 議事録取得失敗: {e}")
        all_gijiroku = {d: {} for d in meetings_by_date}

    # 3. Lステップを全日付まとめて取得
    print("\n3. Lステップを検索中...")
    try:
        all_lstep = get_lstep_links(meetings_by_date)
    except Exception as e:
        print(f"⚠️ Lステップ取得失敗: {e}")
        all_lstep = {d: {} for d in meetings_by_date}

    # 4. 各日付のHTMLを生成
    print("\n4. HTML生成中...")
    for offset in range(GENERATE_DAYS):
        target = TODAY + datetime.timedelta(days=offset)
        date_filename = target.strftime("%Y-%m-%d") + ".html"
        d_str = f"{target.year}年{target.month}月{target.day}日"
        try:
            meetings = meetings_by_date[target]
            gijiroku = all_gijiroku.get(target, {})
            html = generate_html(meetings, gijiroku, all_lstep.get(target, {}), target)
            with open(date_filename, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"   ✅ {date_filename} ({len(meetings)}件)")
        except Exception as e:
            print(f"   ❌ {d_str} エラー: {e}")
            wday = ["月","火","水","木","金","土","日"][target.weekday()]
            error_html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<title>エラー</title>
<style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f5f6f8}}
.box{{background:#fff;border-radius:12px;padding:40px;text-align:center;border:1px solid #e8eaf0;max-width:400px}}
h1{{color:#ea4335;font-size:18px;margin-bottom:12px}}p{{color:#555;font-size:13px;line-height:1.6}}</style>
</head><body><div class="box">
<h1>⚠️ 生成エラー</h1>
<p>{d_str}（{wday}）のブリーフィング生成に失敗しました。</p>
<p style="margin-top:12px;color:#aaa;font-size:11px">{e}</p>
</div></body></html>"""
            with open(date_filename, "w", encoding="utf-8") as f:
                f.write(error_html)

    print("\n5. index.html 再生成中...")
    regenerate_index(meetings_by_date)
