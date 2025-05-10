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

# ---------- Sicheren Rerun abfangen ----------
if st.session_state.get("trigger_rerun"):
    st.session_state["trigger_rerun"] = False
    st.experimental_rerun()

# ---------- Session State nutzen statt query_params ----------
page = st.session_state.get("page", "login")
token = st.session_state.get("token")
email = st.session_state.get("email")
user_id = st.session_state.get("user_id")

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
    return "offen"

def toggle_status(testcase_id, user_id, week, year, current_status):
    new_status = "erledigt" if current_status == "offen" else "offen"
    url = f"{SUPABASE_URL}/rest/v1/testcase_status?testcase_id=eq.{testcase_id}&user_id=eq.{user_id}&calendar_week=eq.{week}&year=eq.{year}"
    headers = HEADERS.copy()
    headers["Prefer"] = "return=minimal"
    payload = { "status": new_status }
    requests.patch(url, headers=headers, json=payload)

# ---------- Login ----------
if "email" not in st.session_state:
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
            profile = get_user_profile(user_email)
            if profile:
                st.session_state["token"] = access_token
                st.session_state["email"] = user_email
                st.session_state["user_id"] = profile["id"]
                st.session_state["page"] = "home"
                st.experimental_rerun()
        else:
            st.error("Login fehlgeschlagen.")

# ---------- Startseite ----------
elif st.session_state.get("page") == "home" and email:
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
                task_info = task["testcases"]
                current_status = get_status(task["testcase_id"], u_id, week, year)
                color = "#fdd" if current_status == "offen" else "#dfd" if current_status == "erledigt" else "#eee"
                key = f"{task['testcase_id']}-{u_id}"
                with st.form(key=key):
                    st.markdown(f"""
                        <button type='submit' style='width:100%; border:none; background-color:{color}; padding:12px; border-radius:8px; cursor:pointer;'>
                            <strong>{task_info['title']}</strong><br>
                            <span style='font-size: 12px;'>🛈 Beschreibung anzeigen</span>
                        </button>
                    """, unsafe_allow_html=True)
                    if st.form_submit_button(" "):
                        toggle_status(task["testcase_id"], u_id, week, year, current_status)
                        st.session_state["trigger_rerun"] = True
                    with st.expander("🛈 Beschreibung anzeigen"):
                        st.markdown(task_info["description"])

    if st.button("Logout"):
        for key in ["email", "token", "user_id", "page"]:
            st.session_state.pop(key, None)
        st.experimental_rerun()

else:
    st.warning("Bitte einloggen.")
