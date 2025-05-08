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

def add_user(username, password):
    hashed_pw = stauth.Hasher([password]).generate()[0]
    payload = {"username": username, "password": hashed_pw}
    res = requests.post(f"{SUPABASE_URL}/rest/v1/users", headers=HEADERS, json=payload)
    return res.status_code == 201

def add_task(description, frequency, assigned_to):
    payload = {
        "description": description,
        "frequency": frequency,
        "assigned_to": assigned_to,
        "last_done": None
    }
    res = requests.post(f"{SUPABASE_URL}/rest/v1/tasks", headers=HEADERS, json=payload)
    return res.status_code == 201

def get_due_tasks(username):
    url = f"{SUPABASE_URL}/rest/v1/tasks?assigned_to=eq.{username}"
    res = requests.get(url, headers=HEADERS)
    tasks = []
    if res.status_code == 200:
        today = datetime.date.today()
        for row in res.json():
            freq = row["frequency"]
            last_done = row["last_done"]
            delta_days = {"weekly": 7, "biweekly": 14, "monthly": 30}.get(freq, 7)
            if not last_done or (today - datetime.date.fromisoformat(last_done)).days >= delta_days:
                tasks.append({"id": row["id"], "description": row["description"]})
    return tasks

def mark_task_done(task_id):
    today = datetime.date.today().isoformat()
    url = f"{SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}"
    payload = {"last_done": today}
    res = requests.patch(url, headers=HEADERS, json=payload)
    return res.status_code == 204

# ---------- Authentifizierung ----------
users = get_users()
authenticator = stauth.Authenticate(
    credentials={
        "usernames": {
            user: {
                "email": f"{user}@example.com",
                "name": user,
                "password": pwd
            } for user, pwd in users.items()
        }
    },
    cookie_name="testcase_login",
    key="abcdef",
    cookie_expiry_days=1
)

st.title("Login")
auth_status = authenticator.login(location="main")

if auth_status:
    username = authenticator.username
    st.sidebar.success(f"Eingeloggt als {username}")
    authenticator.logout("Logout", "sidebar")

    if username == "admin":
        st.header("Admin Bereich")

        # Nutzerverwaltung
        st.subheader("Neuen Nutzer anlegen")
        new_user = st.text_input("Benutzername")
        new_pass = st.text_input("Passwort", type="password")
        if st.button("Benutzer speichern"):
            if add_user(new_user, new_pass):
                st.success("Benutzer erfolgreich gespeichert.")
            else:
                st.error("Fehler beim Speichern des Benutzers.")

        # Testcases anlegen
        st.subheader("Testcase anlegen")
        desc = st.text_input("Beschreibung")
        freq = st.selectbox("Frequenz", ["weekly", "biweekly", "monthly"])
        assigned_to = st.selectbox("Zuweisung an", list(users.keys()))
        if st.button("Testcase speichern"):
            if add_task(desc, freq, assigned_to):
                st.success("Testcase gespeichert.")
            else:
                st.error("Fehler beim Speichern des Testcases.")

    else:
        st.header(f"Deine Aufgaben, {username}")
        tasks = get_due_tasks(username)
        if not tasks:
            st.info("Keine offenen Aufgaben.")
        for i, task in enumerate(tasks):
            with st.expander(task["description"]):
                if st.button(f"Als erledigt markieren #{i}"):
                    if mark_task_done(task["id"]):
                        st.success("Aufgabe erledigt.")
                    else:
                        st.error("Fehler beim Aktualisieren.")
else:
    st.warning("Bitte logge dich ein.")
