import streamlit as st
import requests
import urllib.parse
import datetime
import pandas as pd

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
def get_current_week():
    today = datetime.date.today()
    return today.isocalendar().week, today.isocalendar().year

def get_user_profile(email):
    res = requests.get(f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}", headers=HEADERS)
    return res.json()[0] if res.status_code == 200 and res.json() else None

def get_all_users():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/users?select=email,username,role", headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def get_scheduled_testcases(week, year):
    url = f"{SUPABASE_URL}/rest/v1/testcase_schedule?calendar_week=eq.{week}&year=eq.{year}&select=testcase_id,user_email,testcases(id,title,tooltip)"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def get_status(tc_id, user_email, week, year):
    url = f"{SUPABASE_URL}/rest/v1/testcase_status?testcase_id=eq.{tc_id}&user_email=eq.{user_email}&calendar_week=eq.{week}&year=eq.{year}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200 and res.json():
        return res.json()[0]["status"]
    return "offen"

def toggle_status(tc_id, user_email, week, year, current_status):
    new_status = "erledigt" if current_status == "offen" else "offen"
    data = {
        "testcase_id": tc_id,
        "user_email": user_email,
        "year": year,
        "calendar_week": week,
        "status": new_status
    }
    h = HEADERS.copy()
    h["Prefer"] = "resolution=merge-duplicates"
    requests.post(f"{SUPABASE_URL}/rest/v1/testcase_status", headers=h, json=data)

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

    week, year = get_current_week()
    st.title(f"Testcases – KW {week}")

    users = [u for u in get_all_users() if u["role"] in ("Tester", "Admin")]
    scheduled = get_scheduled_testcases(week, year)

    # Gruppieren nach Testcase ID
    testcase_map = {}
    for item in scheduled:
        tc_id = item["testcase_id"]
        if tc_id not in testcase_map:
            testcase_map[tc_id] = {
                "title": item["testcases"]["title"],
                "tooltip": item["testcases"]["tooltip"],
                "users": {}
            }
        testcase_map[tc_id]["users"][item["user_email"]] = item["testcases"]["id"]

    header = [u["username"] for u in users]
    data = []
    for tc_id, content in testcase_map.items():
        row = [content["title"]]
        for u in users:
            u_email = u["email"]
            status = get_status(tc_id, u_email, week, year)
            label = "✅" if status == "erledigt" else "⛔"
            color = "#dfd" if status == "erledigt" else "#fdd"
            is_active = u_email == email
            if u_email in content["users"]:
                if st.button(f"{label} ({tc_id})", key=f"{tc_id}-{u_email}") and is_active:
                    toggle_status(tc_id, u_email, week, year, status)
                    st.experimental_rerun()
                row.append(f"{label}")
            else:
                row.append("–")
        data.append(row)

    col_headers = ["Testcase"] + header
    st.markdown("### Geplante Testcases")
    st.markdown("<style>td, th {text-align: center !important;}</style>", unsafe_allow_html=True)
    df = pd.DataFrame(data, columns=col_headers)
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.warning("Bitte neu einloggen.")
    st.markdown("<meta http-equiv='refresh' content='0;url=/?page=login'>", unsafe_allow_html=True)
    st.stop()
