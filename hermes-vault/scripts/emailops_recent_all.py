"""Email Ops — Fetch all recent emails from all accounts. Runs 4x daily."""
import json, os, re, sys, time, urllib.request
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

HERMES = Path(os.environ.get("LOCALAPPDATA", "")) / "hermes"
EMAILOPS = HERMES / "emailops"
EMAILOPS.mkdir(parents=True, exist_ok=True)
INDEX_FILE = EMAILOPS / "email_index.json"
ENV_FILE = HERMES / "hermes-agent" / ".env"
AUTH_JSON = HERMES / "auth.json"

def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

load_env()

ACCOUNTS = {
    "silvak2023@outlook.com": {"type": "outlook", "label": "Primary Business"},
    "silvakretail@gmail.com": {"type": "gmail", "label": "Secondary Business"},
    "newtonstore0@gmail.com": {"type": "gmail", "label": "Shop"},
    "sva23@live.co.uk": {"type": "outlook", "label": "Historical"},
    "shivakand115@gmail.com": {"type": "gmail", "label": "Shivakand"},
    "siyanthank@gmail.com": {"type": "gmail", "label": "Siyanthan"},
    "hermsilva26@gmail.com": {"type": "gmail", "label": "Hermes Silva"},
    "silvak2620@gmail.com": {"type": "gmail", "label": "Silva Extra"},
}

def load_index():
    if INDEX_FILE.exists():
        raw = INDEX_FILE.read_text(encoding="utf-8-sig")
        if not raw.strip():
            return {"last_run": None, "accounts": {}}
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                data.setdefault("last_run", None)
                data.setdefault("accounts", {})
                return data
        except json.JSONDecodeError:
            corrupt = INDEX_FILE.with_suffix(".json.corrupt")
            try:
                INDEX_FILE.replace(corrupt)
            except OSError:
                pass
    return {"last_run": None, "accounts": {}}

def save_index(idx):
    tmp = INDEX_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(idx, indent=2, default=str), encoding="utf-8")
    tmp.replace(INDEX_FILE)

def refresh_graph_token():
    client_id = os.environ.get("MS_GRAPH_CLIENT_ID")
    refresh = os.environ.get("MICROSOFT_GRAPH_REFRESH_TOKEN")
    if not client_id or not refresh:
        print("  [WARN] No refresh token available for Graph")
        return False
    tenant = os.environ.get("MS_GRAPH_TENANT_ID", "common")
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = f"client_id={client_id}&refresh_token={refresh}&grant_type=refresh_token&scope=https://graph.microsoft.com/Mail.ReadWrite%20https://graph.microsoft.com/Mail.Send%20https://graph.microsoft.com/User.Read%20offline_access"
    req = urllib.request.Request(url, data=data.encode(), method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        tokens = json.loads(resp.read())
        os.environ["MICROSOFT_GRAPH_TOKEN"] = tokens["access_token"]
        if "refresh_token" in tokens:
            os.environ["MICROSOFT_GRAPH_REFRESH_TOKEN"] = tokens["refresh_token"]
        print("  [OK] Graph token refreshed")
        return True
    except Exception as e:
        print(f"  [ERROR] Token refresh failed: {e}")
        return False

def graph_get(url, retry=1):
    token = os.environ.get("MICROSOFT_GRAPH_TOKEN")
    if not token:
        print("  [SKIP] MICROSOFT_GRAPH_TOKEN not set")
        return None
    headers = {"Authorization": f"Bearer {token}", "Prefer": "outlook.body-content-type='text'"}
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.request.HTTPError as e:
        if e.code == 401 and retry > 0:
            print("  Token expired, refreshing...")
            if refresh_graph_token():
                return graph_get(url, retry=0)
        print(f"  [ERROR] HTTP {e.code}: {e}")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None

def fetch_outlook_graph(account):
    url = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$top=20&$select=subject,from,receivedDateTime,hasAttachments,isRead,bodyPreview&$orderby=receivedDateTime%20desc"
    data = graph_get(url)
    if not data:
        return []
    msgs = data.get("value", [])
    for m in msgs:
        f = m.get("from", {}) or {}
        addr = (f.get("emailAddress", {}) or {}).get("address", "unknown")
        m["_from"] = addr
    return msgs

def fetch_gmail_imap(account):
    acct_name = account.split("@")[0]
    password = os.environ.get(f"GMAIL_APP_PW_{acct_name}")
    if not password:
        print(f"  [SKIP] no app password for {acct_name} (set GMAIL_APP_PW_{acct_name} in .env)")
        return []
    import imaplib, email
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(account, password)
        mail.select("INBOX")
        status, ids = mail.search(None, "ALL")
        if status != "OK":
            mail.logout()
            return []
        ids = ids[0].split()[-20:]
        msgs = []
        for mid in ids:
            status, data = mail.fetch(mid, "(RFC822)")
            if status != "OK":
                continue
            raw = email.message_from_bytes(data[0][1])
            msgs.append({
                "subject": raw["Subject"] or "",
                "_from": raw["From"] or "",
                "from": raw["From"] or "",
                "date": str(parsedate_to_datetime(raw["Date"])) if raw["Date"] else "",
                "hasAttachments": bool(raw.get_payload() and not isinstance(raw.get_payload(), str)) if raw.is_multipart() else False,
                "bodyPreview": str(raw.get_payload())[:200] if isinstance(raw.get_payload(), str) else "",
            })
        mail.logout()
        return msgs
    except Exception as e:
        print(f"  [ERROR] {account} IMAP: {e}")
        return []

def save_account_emails(account, msgs):
    acct_dir = EMAILOPS / account.split("@")[0]
    acct_dir.mkdir(parents=True, exist_ok=True)
    batch_file = acct_dir / f"emails_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    batch_file.write_text(json.dumps(msgs, indent=2, default=str))
    return batch_file

def main():
    print("=== Email Ops - 4x Daily Fetch ===")
    print(f"Time: {datetime.now().isoformat()}\n")
    index = load_index()
    total = 0
    for email_addr, cfg in ACCOUNTS.items():
        print(f"[{cfg['label']}] {email_addr} ({cfg['type']})")
        if cfg["type"] == "outlook":
            msgs = fetch_outlook_graph(email_addr)
        elif cfg["type"] == "gmail":
            msgs = fetch_gmail_imap(email_addr)
        else:
            msgs = []
        if msgs:
            path = save_account_emails(email_addr, msgs)
            print(f"  Saved {len(msgs)} emails -> {path}")
            for m in msgs[:3]:
                print(f"    - {m.get('subject', 'No subject')[:80]} - {m.get('_from', '')[:40]}")
            total += len(msgs)
        else:
            print(f"  0 new emails")
        print()
    index["last_run"] = datetime.now().isoformat()
    save_index(index)
    print(f"=== Done - {total} emails fetched across {len(ACCOUNTS)} accounts ===")
    return total

if __name__ == "__main__":
    main()
