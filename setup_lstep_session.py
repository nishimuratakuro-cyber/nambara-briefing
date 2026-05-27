"""
Lステップのセッションを保存する。
reCAPTCHAがあるため手動ログイン後にセッションをJSONとして保存。
セッション期限切れ時に再実行してください。

実行後:
  gh secret set LSTEP_SESSION < lstep_session.json
"""
from playwright.sync_api import sync_playwright
import json

LSTEP_LOGIN_URL = "https://manager.linestep.net/account/login"
SESSION_FILE = "lstep_session.json"

print("Lステップセッション設定")
print("=" * 40)
print(f"ブラウザで {LSTEP_LOGIN_URL} を開きます。")
print("reCAPTCHAを解除してログインを完了してください。")
print("ログイン後、Enterを押してセッションを保存します。")
print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1400, "height": 900})
    page = context.new_page()

    page.goto(LSTEP_LOGIN_URL)

    input("ブラウザでログインが完了したらEnterを押してください...")

    if "login" in page.url:
        print("⚠️ まだログインページにいます。ログインを完了してから再度Enterを押してください。")
        input("Enter: ")

    context.storage_state(path=SESSION_FILE)
    print(f"✅ セッションを {SESSION_FILE} に保存しました。")
    print()
    print("次のコマンドでGitHub Secretに登録してください:")
    print(f"  gh secret set LSTEP_SESSION < {SESSION_FILE}")

    browser.close()
