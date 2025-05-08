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

# ---------- Session-Fix ----------
if "force_rerun" in st.session_state and st.session_state.force_rerun:
    st.session_state.force_rerun = False
    st.write("🔁 App wird neu geladen...")
    st.experimental_rerun()
    st.stop()

# ---------- Session-Init ----------
if "session" not in st.session_state:
    st.session_state["session"] = None

# ---------- Login ----------
if not st.session_state["session"]:
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
            st.session_state["force_rerun"] = True
            st.stop()
        else:
            st.error("Login fehlgeschlagen. Bitte überprüfe E-Mail und Passwort.")
else:
    st.sidebar.success("✅ Eingeloggt")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"session": None}))

    user_email = st.session_state["session"]["user"]["email"]
    st.title(f"Willkommen, {user_email}!")

    st.info("Hier kannst du jetzt Aufgaben, Testcases usw. einbinden.")
