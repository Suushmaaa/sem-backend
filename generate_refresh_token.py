from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes for Google Ads API
SCOPES = ["https://www.googleapis.com/auth/adwords"]

CLIENT_ID = "864748201338-ok88spfkp4u2b4djp0kpgh7ojjbvm3f4.apps.googleusercontent.com"
CLIENT_SECRET = "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"

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=SCOPES,
)

credentials = flow.run_local_server(port=8080)

print("Refresh Token:", credentials.refresh_token)
