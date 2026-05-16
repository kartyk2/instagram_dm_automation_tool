# 📲 Instagram AutoDM (FastAPI)

Auto-reply to Instagram DMs using keyword matching. Built with Python + FastAPI, hosted on Railway.

---

## 📁 Project Structure

```
instagram-autodm-py/
├── main.py                 → FastAPI app entry point
├── routes/
│   └── webhook.py          → Meta webhook verification + incoming DM handler
├── services/
│   ├── matcher.py          → Keyword → reply matching logic
│   └── instagram.py        → Sends replies via Instagram Graph API
├── config/
│   └── rules.json          → ✏️  YOUR keyword rules (edit this!)
├── requirements.txt
├── Procfile                → Railway start command
└── .env.example            → Credentials template
```

---

## 🔑 Only 2 Credentials Needed

Add these in **Railway → Project → Variables**:

```
IG_ACCESS_TOKEN       → from Meta Graph API Explorer
WEBHOOK_VERIFY_TOKEN  → any random string you make up (e.g. mysecret123)
```

---

## 🚀 Deployment Steps

### 1 — Deploy to Railway
1. Push this repo to GitHub
2. [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add the 2 env vars above under **Project → Variables**
4. Copy your Railway public URL: `https://your-app.up.railway.app`

### 2 — Create Meta Developer App
1. [developers.facebook.com](https://developers.facebook.com) → My Apps → Create App
2. Choose **Other** → **Business**
3. Add Product → **Messenger** → Set Up
4. Under Messenger → Instagram Settings: connect your Facebook Page

### 3 — Get Your Access Token
1. Meta App Dashboard → **Tools → Graph API Explorer**
2. Add permissions: `instagram_manage_messages`, `pages_messaging`
3. Click **Generate Access Token** → copy it → paste as `IG_ACCESS_TOKEN` in Railway

### 4 — Set Up Webhook
1. Meta App Dashboard → Messenger → Instagram Settings → Webhooks
2. Callback URL: `https://your-app.up.railway.app/webhook`
3. Verify Token: same value as your `WEBHOOK_VERIFY_TOKEN`
4. Click **Verify and Save** → then subscribe to: ✅ `messages`

### 5 — Edit Your Rules
Open `config/rules.json` and customize:

```json
[
  {
    "keywords": ["price", "cost", "how much"],
    "reply": "Pricing starts at $X, DM for details!"
  },
  {
    "keywords": ["collab", "sponsor"],
    "reply": "Email me at you@example.com for collabs 🤝"
  }
]
```

- Keywords are **case-insensitive**
- **First matching rule wins** — put specific rules higher up
- No code changes needed, just edit the JSON

---

## 🧪 Running Locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # fill in your values
uvicorn main:app --reload --port 3000
```

To expose locally for Meta webhook testing:
```bash
ngrok http 3000
# Use the https ngrok URL as your Meta callback URL
```

---

## ⚠️ Limitations to Know

| Issue | Detail |
|---|---|
| 24-hour window | Can only reply within 24h of user's last message |
| App Review | Required by Meta before real users (not test accounts) can trigger it |
| Token expiry | Page Access Tokens expire in 60 days — refresh or use a System User token |
| Rate limits | Don't over-reply — Meta may flag the account |
