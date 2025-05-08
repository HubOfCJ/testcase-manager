import streamlit as st
from supabase import create_client, Client
import os

# ---------- Supabase Zugang ----------
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# ---------- Session State ----------
if "session" not in st.session_state:
    st.session_state["session"] = None

# ---------- Login-Formular ----------
if not st.session_state["session"]:
    st.title("🔐 Login mit Supabase Auth")

    email = st.text_input("E-Mail")
    password = st.text_input("Passwort", type="password")
    login = st.button("Login")

    if login:
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["session"] = auth_response
            st.success("Login erfolgreich!")
            st.experimental_rerun()
        except Exception as e:
            st.error("Login fehlgeschlagen. Bitte überprüfe deine Zugangsdaten.")
else:
    st.sidebar.success("✅ Eingeloggt")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"session": None}))
    
    user = st.session_state["session"].user
    st.title(f"Willkommen, {user['email']}!")

    # Hier kommt deine eigentliche App-Logik rein
    st.info("Hier könntest du Testcases, Aufgaben usw. einbinden.")
