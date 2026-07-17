"""Mark specific emails as read via Microsoft Graph API and Gmail IMAP."""
import json, os, urllib.request, imaplib
from pathlib import Path
from email.header import decode_header

HERMES = Path(os.environ.get("LOCALAPPDATA", "")) / "hermes"
ENV_FILE = HERMES / "hermes-agent" / ".env"

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

# Outlook Graph API - mark as read
def refresh_graph_token():
    client_id = os.environ.get("MS_GRAPH_CLIENT_ID")
    refresh = os.environ.get("MICROSOFT_GRAPH_REFRESH_TOKEN")
    if not client_id or not refresh:
        print("[SKIP] No Graph refresh token")
        return None
    tenant = os.environ.get("MS_GRAPH_TENANT_ID", "common")
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = f"client_id={client_id}&refresh_token={refresh}&grant_type=refresh_token&scope=https://graph.microsoft.com/Mail.ReadWrite%20https://graph.microsoft.com/User.Read%20offline_access"
    req = urllib.request.Request(url, data=data.encode(), method="POST")
    resp = urllib.request.urlopen(req, timeout=30)
    tokens = json.loads(resp.read())
    return tokens["access_token"]

def mark_graph_read(token, msg_id):
    url = f"https://graph.microsoft.com/v1.0/me/messages/{msg_id}"
    body = json.dumps({"isRead": True}).encode()
    req = urllib.request.Request(url, data=body, method="PATCH",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        print(f"  Graph error: {e}")
        return False

def search_and_mark_gmail_read(account, password, search_terms):
    """Search Gmail inbox for matching subjects and mark as read."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(account, password)
        mail.select("INBOX")
        count = 0
        for term in search_terms:
            status, ids = mail.search(None, f'(SUBJECT "{term}")')
            if status == "OK" and ids[0]:
                for mid in ids[0].split():
                    # Add \Seen flag to mark as read
                    mail.store(mid, "+FLAGS", "\\Seen")
                    count += 1
                    print(f"  Gmail marked read: {term} (msg {mid.decode()})")
        mail.logout()
        return count
    except Exception as e:
        print(f"  Gmail IMAP error: {e}")
        return 0

print("=== Marking emails as read ===\n")

# --- Outlook via Graph API ---
print("[Outlook] Refreshing token...")
token = refresh_graph_token()
if token:
    print("[Outlook] Token OK\n")
    
    # PayPoint settlement + Funding Options + Property alerts on silvak2023
    outlook_ids = [
        # PayPoint settlement notice
        "AQMkADAwATM3ZmYAZS03MTYyLTFiYgA0LTAwAi0wMAoARgAAA3myr7mBT5xFrNFoIwa3rY4HADvTGpUPPl1Fu5MfImKdQm4AAAIBDAAAADvTGpUPPl1Fu5MfImKdQm4AAnRDnzwAAAA=",
        # Funding Options - Recovery Loan Scheme
        "AQMkADAwATM3ZmYAZS03MTYyLTFiYgA0LTAwAi0wMAoARgAAA3myr7mBT5xFrNFoIwa3rY4HADvTGpUPPl1Fu5MfImKdQm4AAAIBDAAAADvTGpUPPl1Fu5MfImKdQm4AAnRD0IAAAA=",
        # Funding Options - Trade plan grow
        "AQMkADAwATM3ZmYAZS03MTYyLTFiYgA0LTAwAi0wMAoARgAAA3myr7mBT5xFrNFoIwa3rY4HADvTGpUPPl1Fu5MfImKdQm4AAAIBDAAAADvTGpUPPl1Fu5MfImKdQm4AAnRDnzkAAAA=",
        # Property alert deactivated
        "AQMkADAwATM3ZmYAZS03MTYyLTFiYgA0LTAwAi0wMAoARgAAA3myr7mBT5xFrNFoIwa3rY4HADvTGpUPPl1Fu5MfImKdQm4AAAIBDAAAADvTGpUPPl1Fu5MfImKdQm4AAnRD0MAAAA=",
        # Property match Euston Grove
        "AQMkADAwATM3ZmYAZS03MTYyLTFiYgA0LTAwAi0wMAoARgAAA3myr7mBT5xFrNFoIwa3rY4HADvTGpUPPl1Fu5MfImKdQm4AAAIBDAAAADvTGpUPPl1Fu5MfImKdQm4AAnRDnz0AAAA=",
        # Rentaroof Euston Grove (from earlier batch, same thread)
        "AQMkADAwATM3ZmYAZS03MTYyLTFiYgA0LTAwAi0wMAoARgAAA3myr7mBT5xFrNFoIwa3rY4HADvTGpUPPl1Fu5MfImKdQm4AAAIBDAAAADvTGpUPPl1Fu5MfImKdQm4AAnRDnz4AAAA=",
    ]
    
    marked = 0
    for mid in outlook_ids:
        if mark_graph_read(token, mid):
            marked += 1
            print(f"  Graph marked read: {mid[:40]}...")
    print(f"\n[Outlook] {marked}/{len(outlook_ids)} emails marked as read\n")
else:
    print("[Outlook] SKIPPED - no token\n")

# --- Gmail IMAP ---
gmail_accounts = {
    "silvakretail@gmail.com": ["Security alert"],
    "newtonstore0@gmail.com": ["settlement notice", "Funding Options", "PayPoint"],
    "hermsilva26@gmail.com": ["Langdale Place", "Rent arrears", "BACS payment"],
}

for acct, terms in gmail_accounts.items():
    acct_name = acct.split("@")[0]
    password = os.environ.get(f"GMAIL_APP_PW_{acct_name}")
    if not password:
        print(f"[Gmail] {acct} - SKIP (no app password)")
        continue
    print(f"[Gmail] {acct} - marking matching emails as read...")
    n = search_and_mark_gmail_read(acct, password, terms)
    print(f"  Marked {n} emails\n")

print("=== Done ===")
