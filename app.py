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

# ---------- Session initialisieren ----------
if "session" not in st.session_state:
    st.session_state["session"] = None

# ---------- Login & Rerun Logik ----------
if "just_logged_in" not in st.session_state:
    st.session_state["just_logged_in"] = False

# ---------- Rerun sicher auslösen ----------
if st.session_state["just_logged_in"]:
    st.session_state["just_logged_in"] = False
    st.experimental_rerun()

# ---------- Login ----------
if st.session_state["session"] is None:
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
            st.session_state["session"] = res.json()
            st.session_state["just_logged_in"] = True
            st.success("Login erfolgreich! Weiterleitung...")
        else:
            st.error("Login fehlgeschlagen. Bitte überprüfe E-Mail und Passwort.")
else:
    st.sidebar.success("✅ Eingeloggt")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"session": None}))

    user_email = st.session_state["session"]["user"]["email"]
    st.title(f"Willkommen, {user_email}!")

    st.info("Hier kannst du deine App-Funktionen einfügen.")
