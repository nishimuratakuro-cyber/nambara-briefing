"""
★ 初回1回だけ実行するスクリプト ★
GoogleカレンダーAPIのトークンを取得してGitHub Secretsに登録する値を表示します。
"""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# client_secret.json のパスを指定
CLIENT_SECRET_FILE = "client_secret.json"

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
creds = flow.run_local_server(port=0)

token_data = {
    "token":         creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri":     creds.token_uri,
    "client_id":     creds.client_id,
    "client_secret": creds.client_secret,
    "scopes":        list(creds.scopes),
}

print("\n" + "="*60)
print("✅ 認証成功！以下の値をGitHub Secretsに登録してください")
print("="*60)
print("\n【Secret名】GOOGLE_TOKEN")
print("【値】↓ここから↓")
print(json.dumps(token_data))
print("↑ここまで↑\n")
