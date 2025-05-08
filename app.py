import streamlit as st
import requests

# ---------- Supabase Zugang ----------
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
AUTH_ENDPOINT = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json"
}

# ---------- Session State Setup ----------
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "just_logged_in" not in st.session_state:
    st.session_state["just_logged_in"] = False

# ---------- Sanftes Rerun nach Login ----------
if st.session_state["just_logged_in"]:
    st.session_state["just_logged_in"] = False
    st.experimental_rerun()

# ---------- Login ----------
if not st.session_state["access_token"]:
    st.title("🔐 Login mit Supabase Auth")

    email = st.text_input("E-Mail")
    password = st.text_input("Passwort", type="password")

    if st.button("Login"):
        payload = {
            "email": email,
            "password": password
        }
        res = requests.post(AUTH_ENDPOINT, headers=HEADERS, json=payload)
        if res.status_code == 200:
            data = res.json()
            st.session_state["access_token"] = data["access_token"]
            st.session_state["user_email"] = data["user"]["email"]
            st.session_state["just_logged_in"] = True
            st.success("Login erfolgreich! Einen Moment...")
            st.stop()
        else:
            st.error("Login fehlgeschlagen. Bitte überprüfe E-Mail und Passwort.")
else:
    st.sidebar.success(f"✅ Eingeloggt als {st.session_state['user_email']}")
    if st.sidebar.button("Logout"):
        st.session_state["access_token"] = None
        st.session_state["user_email"] = None
        st.experimental_rerun()

    st.title(f"Willkommen, {st.session_state['user_email']}!")
    st.info("Hier kannst du deine App-Funktionen einfügen.")
