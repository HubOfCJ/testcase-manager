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

# ---------- Session State ----------
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

# ---------- URL Parameter-Steuerung ----------
params = st.query_params
page = params.get("page", "login")

# ---------- Login-Seite ----------
if page == "login" and not st.session_state["access_token"]:
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
            st.success("Login erfolgreich – Weiterleitung...")
            st.markdown("<meta http-equiv='refresh' content='0;url=/?page=home'>", unsafe_allow_html=True)
            st.stop()
        else:
            st.error("Login fehlgeschlagen. Bitte überprüfe E-Mail und Passwort.")

# ---------- App-Hauptbereich ----------
elif page == "home" and st.session_state["access_token"]:
    user_email = st.session_state.get("user_email", "Unbekannt")

    st.sidebar.success(f"✅ Eingeloggt als {user_email}")
    if st.sidebar.button("Logout"):
        st.session_state["access_token"] = None
        st.session_state["user_email"] = None
        st.markdown("<meta http-equiv='refresh' content='0;url=/?page=login'>", unsafe_allow_html=True)
        st.stop()

    st.title(f"Willkommen, {user_email}!")
    st.info("Hier kannst du deine App-Funktionen einfügen.")

else:
    st.warning("Bitte logge dich ein.")
    st.markdown("<meta http-equiv='refresh' content='0;url=/?page=login'>", unsafe_allow_html=True)
    st.stop()
