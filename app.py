import streamlit as st
import streamlit_authenticator as stauth
import json
import datetime
from pathlib import Path

# ---------- Konfiguration ----------
DATA_FILE = 'data.json'
FREQUENCIES = {'weekly': 7, 'biweekly': 14, 'monthly': 30}

# ---------- Hilfsfunktionen ----------
def load_data():
    if not Path(DATA_FILE).exists():
        with open(DATA_FILE, 'w') as f:
            json.dump({'users': {}, 'tasks': []}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_due_tasks(tasks, username):
    today = datetime.date.today()
    due = []
    for task in tasks:
        if task['assigned_to'] == username:
            last_done = datetime.date.fromisoformat(task['last_done']) if task['last_done'] else None
            delta_days = FREQUENCIES.get(task['frequency'], 7)
            if not last_done or (today - last_done).days >= delta_days:
                due.append(task)
    return due

# ---------- Authentifizierung ----------
data = load_data()

hashed_passwords = {user: stauth.Hasher([pwd]).generate()[0] for user, pwd in data['users'].items()}
authenticator = stauth.Authenticate(
    credentials={"usernames": {user: {"email": f"{user}@example.com", "name": user, "password": pwd} for user, pwd in hashed_passwords.items()}},
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
        st.subheader("Nutzer anlegen")
        new_user = st.text_input("Benutzername")
        new_pass = st.text_input("Passwort", type="password")
        if st.button("Benutzer speichern"):
            data['users'][new_user] = new_pass
            save_data(data)
            st.success("Benutzer gespeichert")

        # Testcases anlegen
        st.subheader("Testcase anlegen")
        desc = st.text_input("Beschreibung")
        freq = st.selectbox("Frequenz", list(FREQUENCIES.keys()))
        assigned_to = st.selectbox("Zuweisung an", list(data['users'].keys()))
        if st.button("Testcase speichern"):
            data['tasks'].append({
                'description': desc,
                'frequency': freq,
                'assigned_to': assigned_to,
                'last_done': None
            })
            save_data(data)
            st.success("Testcase gespeichert")

    else:
        st.header(f"Deine Aufgaben, {username}")
        user_tasks = get_due_tasks(data['tasks'], username)

        if not user_tasks:
            st.info("Keine offenen Aufgaben.")
        for i, task in enumerate(user_tasks):
            with st.expander(task['description']):
                if st.button(f"Als erledigt markieren #{i}"):
                    task['last_done'] = str(datetime.date.today())
                    save_data(data)
                    st.success("Aufgabe als erledigt markiert")

else:
    st.warning("Bitte logge dich ein.")
