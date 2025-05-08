import streamlit as st
import requests
import urllib.parse

# ---------- Supabase Zugang ----------
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
AUTH_ENDPOINT = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json"
}

# ---------- URL Parameter einlesen ----------
params = st.query_params
page = params.get("page", "login")
token = params.get("token", None)
email = params.get("email", None)

# ---------- Login-Seite ----------
if page == "login":
    st.title("🔐 Login mit Supabase Auth")

    email_input = st.text_input("E-Mail")
    password_input = st.text_input("Passwort", type="password")

    if st.button("Login"):
        payload = {
            "email": email_input,
            "password": password_input
        }
        res = requests.post(AUTH_ENDPOINT, headers=HEADERS, json=payload)
        if res.status_code == 200:
            data = res.json()
            access_token = data["access_token"]
            user_email = data["user"]["email"]
            url = f"/?page=home&token={access_token}&email={urllib.parse.quote(user_email)}"
            st.success("Login erfolgreich! Weiterleitung...")
            st.markdown(f"<meta http-equiv='refresh' content='0;url={url}'>", unsafe_allow_html=True)
            st.stop()
        else:
            st.error("Login fehlgeschlagen. Bitte überprüfe E-Mail und Passwort.")

# ---------- App-Hauptbereich ----------
elif page == "home" and token and email:
    st.sidebar.success(f"✅ Eingeloggt als {email}")
    logout_url = "/?page=login"
    if st.sidebar.button("Logout"):
        st.markdown(f"<meta http-equiv='refresh' content='0;url={logout_url}'>", unsafe_allow_html=True)
        st.stop()

    st.title(f"Willkommen, {email}!")
    st.info("Hier kannst du deine App-Funktionen einfügen.")

else:
    st.warning("Session ungültig oder abgelaufen. Bitte erneut einloggen.")
    st.markdown("<meta http-equiv='refresh' content='0;url=/?page=login'>", unsafe_allow_html=True)
    st.stop()
