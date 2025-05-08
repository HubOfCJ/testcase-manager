import streamlit as st
import requests
import urllib.parse

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
email = params.get("email", None")

# ---------- Seiten: Login ----------
if page == "login":
    st.title("🔐 Login mit Supabase Auth")

    email_input = st.text_input("E-Mail")
    password_input = st.text_input("Passwort", type="password")

    if st.button("Login"):
        payload = {
            "email": email_input,
            "password": password_input
        }
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
            st.error("Login fehlgeschlagen. Bitte überprüfe E-Mail und Passwort.")

# ---------- Seiten: Admin ----------
elif page == "admin" and token and email:
    st.sidebar.success(f"✅ Eingeloggt als {email}")
    logout_url = "/?page=login"
    if st.sidebar.button("Logout"):
        st.markdown(f"<meta http-equiv='refresh' content='0;url={logout_url}'>", unsafe_allow_html=True)
        st.stop()

    st.title("🛠️ Admin: Testcases verwalten")

    def get_all_users():
        url = f"{SUPABASE_URL}/auth/v1/users"
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            return [user["email"] for user in res.json()["users"]]
        return []

    def add_testcase(title, tooltip, interval_days, assigned_users):
        testcase_data = {
            "title": title,
            "tooltip": tooltip,
            "interval_days": interval_days
        }
        tc_res = requests.post(f"{SUPABASE_URL}/rest/v1/testcases", headers=HEADERS, json=testcase_data)
        if tc_res.status_code != 201:
            return False, "Fehler beim Speichern des Testcases"

        testcase_id = tc_res.json()[0]["id"]
        assignment_data = [{"testcase_id": testcase_id, "user_email": e} for e in assigned_users]
        assign_res = requests.post(f"{SUPABASE_URL}/rest/v1/testcase_assignments", headers=HEADERS, json=assignment_data)
        if assign_res.status_code not in [201, 204]:
            return False, "Fehler beim Speichern der Zuweisungen"

        return True, "Testcase erfolgreich gespeichert"

    title = st.text_input("Titel für Kachel")
    tooltip = st.text_area("Tooltip-Beschreibung")
    interval_label = st.selectbox("Wiederholungsintervall", ["7 Tage (wöchentlich)", "14 Tage", "30 Tage (monatlich)"])
    interval = int(interval_label.split(" ")[0])
    users = get_all_users()
    assigned_users = st.multiselect("Zuweisung an Nutzer", users)

    if st.button("Testcase speichern"):
        if title and tooltip and assigned_users:
            success, msg = add_testcase(title, tooltip, interval, assigned_users)
            if success:
                st.success(msg)
            else:
                st.error(msg)
        else:
            st.warning("Bitte alle Felder ausfüllen und mindestens einen Nutzer auswählen.")

# ---------- Seiten: Home ----------
elif page == "home" and token and email:
    st.sidebar.success(f"✅ Eingeloggt als {email}")
    logout_url = "/?page=login"
    if st.sidebar.button("Logout"):
        st.markdown(f"<meta http-equiv='refresh' content='0;url={logout_url}'>", unsafe_allow_html=True)
        st.stop()

    st.title(f"Willkommen, {email}!")

    if email == "cj@example.com":
        admin_link = f"/?page=admin&token={token}&email={urllib.parse.quote(email)}"
        st.markdown(f"[🔧 Zum Adminbereich]({admin_link})", unsafe_allow_html=True)

    st.info("Hier kannst du deine App-Funktionen einfügen.")

# ---------- Fallback ----------
else:
    st.warning("Session ungültig oder abgelaufen. Bitte erneut einloggen.")
    st.markdown("<meta http-equiv='refresh' content='0;url=/?page=login'>", unsafe_allow_html=True)
    st.stop()
