import streamlit as st
import requests
import urllib.parse
import datetime

# ---------- Supabase Zugang ----------
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]
AUTH_ENDPOINT = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ---------- URL Parameter ----------
params = st.query_params
page = params.get("page", "login")
token = params.get("token", None)
email = params.get("email", None)

# ---------- Hilfsfunktionen ----------
def get_current_week_and_year():
    today = datetime.date.today()
    return today.isocalendar().week, today.isocalendar().year

def get_user_profile(email):
    res = requests.get(f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}", headers=HEADERS)
    return res.json()[0] if res.status_code == 200 and res.json() else None

def get_all_users():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/users?select=id,username,email", headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def get_assignments_for_week(week, year):
    url = f"{SUPABASE_URL}/rest/v1/testcase_assignments?calendar_week=eq.{week}&year=eq.{year}&select=*,testcases(id,title,description)"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def get_status(testcase_id, user_id, week, year):
    url = f"{SUPABASE_URL}/rest/v1/testcase_status?testcase_id=eq.{testcase_id}&user_id=eq.{user_id}&calendar_week=eq.{week}&year=eq.{year}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200 and res.json():
        return res.json()[0]["status"]
    return None

# ---------- Login ----------
if page == "login":
    st.title("🔐 Login zum Testcase-Manager")
    email_input = st.text_input("E-Mail")
    password_input = st.text_input("Passwort", type="password")
    if st.button("Login"):
        payload = {"email": email_input, "password": password_input}
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
            st.error("Login fehlgeschlagen.")

# ---------- Startseite ----------
elif page == "home" and token and email:
    profile = get_user_profile(email)
    if not profile:
        st.error("Benutzer nicht gefunden.")
        st.stop()

    week, year = get_current_week_and_year()
    st.title(f"Kalenderwoche {week}")

    users = get_all_users()
    assignments = get_assignments_for_week(week, year)

    if not users:
        st.info("Noch keine Nutzer vorhanden.")
        st.stop()

    user_map = {u["id"]: u for u in users}
    assignment_map = {}
    for item in assignments:
        user_id = item["user_id"]
        if user_id not in assignment_map:
            assignment_map[user_id] = []
        assignment_map[user_id].append(item)

    cols = st.columns(len(users))
    for i, user in enumerate(users):
        u_id = user["id"]
        u_name = user["username"]
        with cols[i]:
            st.markdown(f"**{u_name}**")
            if u_id not in assignment_map:
                st.markdown("–")
                continue
            for task in assignment_map[u_id]:
                status = get_status(task["testcase_id"], u_id, week, year)
                if status == "offen":
                    color = "#fdd"
                elif status == "erledigt":
                    color = "#dfd"
                else:
                    color = "#eee"

                st.markdown(f"""
                    <div style='background-color:{color}; padding:10px; border-radius:8px; margin-bottom:10px;'>
                        <strong>{task['testcases']['title']}</strong><br>
                        <span title="{task['testcases']['description']}">🛈 Details</span>
                    </div>
                """, unsafe_allow_html=True)

else:
    st.warning("Bitte neu einloggen.")
    st.markdown("<meta http-equiv='refresh' content='0;url=/?page=login'>", unsafe_allow_html=True)
    st.stop()
