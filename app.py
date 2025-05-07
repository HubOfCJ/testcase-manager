import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import datetime

# ---------- Konfiguration ----------
DB_FILE = 'data.db'
FREQUENCIES = {'weekly': 7, 'biweekly': 14, 'monthly': 30}

# ---------- Datenbank Setup ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, frequency TEXT, assigned_to TEXT, last_done TEXT)")
    conn.commit()
    conn.close()

init_db()

# ---------- Hilfsfunktionen ----------
def get_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, password FROM users")
    users = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return users

def add_user(username, password):
    hashed_pw = stauth.Hasher([password]).generate()[0]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
    conn.commit()
    conn.close()

def add_task(description, frequency, assigned_to):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (description, frequency, assigned_to, last_done) VALUES (?, ?, ?, ?)",
              (description, frequency, assigned_to, None))
    conn.commit()
    conn.close()

def get_due_tasks(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.date.today()
    due = []
    c.execute("SELECT id, description, frequency, last_done FROM tasks WHERE assigned_to = ?", (username,))
    for row in c.fetchall():
        task_id, description, frequency, last_done = row
        delta_days = FREQUENCIES.get(frequency, 7)
        if not last_done or (today - datetime.date.fromisoformat(last_done)).days >= delta_days:
            due.append({"id": task_id, "description": description})
    conn.close()
    return due

def mark_task_done(task_id):
    today = datetime.date.today().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET last_done = ? WHERE id = ?", (today, task_id))
    conn.commit()
    conn.close()

# ---------- Authentifizierung ----------
users = get_users()
authenticator = stauth.Authenticate(
    credentials={"usernames": {user: {"email": f"{user}@example.com", "name": user, "password": pwd} for user, pwd in users.items()}},
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
            add_user(new_user, new_pass)
            st.success("Benutzer gespeichert")

        # Testcases anlegen
        st.subheader("Testcase anlegen")
        desc = st.text_input("Beschreibung")
        freq = st.selectbox("Frequenz", list(FREQUENCIES.keys()))
        assigned_to = st.selectbox("Zuweisung an", list(users.keys()))
        if st.button("Testcase speichern"):
            add_task(desc, freq, assigned_to)
            st.success("Testcase gespeichert")

    else:
        st.header(f"Deine Aufgaben, {username}")
        tasks = get_due_tasks(username)

        if not tasks:
            st.info("Keine offenen Aufgaben.")
        for i, task in enumerate(tasks):
            with st.expander(task['description']):
                if st.button(f"Als erledigt markieren #{i}"):
                    mark_task_done(task['id'])
                    st.success("Aufgabe als erledigt markiert")

else:
    st.warning("Bitte logge dich ein.")
