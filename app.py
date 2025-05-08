import streamlit as st
import streamlit_authenticator as stauth
import requests
import datetime

# ---------- Supabase-Zugang ----------
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ---------- Hilfsfunktionen ----------
def get_users():
    url = f"{SUPABASE_URL}/rest/v1/users?select=username,password"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return {row['username']: row['password'] for row in res.json()}
    return {}

# ---------- Nutzer laden + Debug ----------
users = get_users()
st.write("Users:", users)

credentials = {
    "usernames": {
        user: {
            "email": f"{user}@example.com",
            "name": user,
            "password": pwd
        } for user, pwd in users.items()
    }
}
st.write("Authenticator credentials:", credentials)

# ---------- Authentifizierung ----------
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="testcase_login",
    key="abcdef",
    cookie_expiry_days=1
)

name, auth_status, username = authenticator.login("Login", "main")
st.write("auth_status:", auth_status)
st.write("username:", username)

if auth_status:
    st.sidebar.success(f"Eingeloggt als {username}")
    authenticator.logout("Logout", "sidebar")
    st.success("✅ Login erfolgreich! Du kannst nun die App erweitern.")
elif auth_status is False:
    st.error("❌ Login fehlgeschlagen. Benutzername oder Passwort falsch?")
else:
    st.info("Bitte logge dich ein.")
