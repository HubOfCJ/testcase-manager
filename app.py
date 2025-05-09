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
subpage = params.get("sub", "")
token = params.get("token", None)
email = params.get("email", None)

# ---------- Hilfsfunktionen ----------
def get_user_profile(email):
    url = f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200 and res.json():
        return res.json()[0]
    return None

def get_current_week():
    today = datetime.date.today()
    return today.isocalendar().week, today.isocalendar().year

# ---------- Login-Seite ----------
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
            st.error("Login fehlgeschlagen. Bitte überprüfe E-Mail und Passwort.")

# ---------- Testcases für Nutzer & Woche ----------
def get_testcases_for_week(email, year, week):
    assigned = requests.get(f"{SUPABASE_URL}/rest/v1/testcase_assignments?user_email=eq.{email}", headers=HEADERS).json()
    all_cases = requests.get(f"{SUPABASE_URL}/rest/v1/testcases", headers=HEADERS).json()
    statuses = requests.get(f"{SUPABASE_URL}/rest/v1/testcase_status?user_email=eq.{email}&year=eq.{year}&calendar_week=eq.{week}", headers=HEADERS).json()

    relevant = []
    for a in assigned:
        tc = next((t for t in all_cases if t['id'] == a['testcase_id']), None)
        if not tc: continue
        last = [s for s in statuses if s['testcase_id'] == tc['id'] and s['status'] == 'erledigt']
        if not last:
            relevant.append((tc, 'offen'))
        else:
            last_item = sorted(last, key=lambda x: (x['year'], x['calendar_week']), reverse=True)[0]
            weeks_since = (year - last_item['year']) * 52 + (week - last_item['calendar_week'])
            if weeks_since >= tc['interval_weeks']:
                stat_now = [s for s in statuses if s['testcase_id'] == tc['id']]
                stat = stat_now[0]['status'] if stat_now else 'offen'
                relevant.append((tc, stat))
    return relevant

def all_done(testcases):
    return all(status == 'erledigt' for _, status in testcases)

# ---------- Startseite ----------
if page == "home" and token and email:
    user = get_user_profile(email)
    if not user:
        st.error("Benutzerprofil nicht gefunden.")
        st.stop()

    username = user.get("username")
    role = user.get("role")
    week, year = get_current_week()

    st.sidebar.success(f"✅ Eingeloggt als {email}")
    if st.sidebar.button("Logout"):
        st.markdown("<meta http-equiv='refresh' content='0;url=/?page=login'>", unsafe_allow_html=True)
        st.stop()

    st.title(f"Willkommen, {username}!")
    st.subheader(f"📆 Kalenderwoche {week}")

    if role == "Admin":
        admin_link = f"/?page=admin&token={token}&email={urllib.parse.quote(email)}"
        st.markdown(f"[🔧 Zum Adminbereich]({admin_link})", unsafe_allow_html=True)

    # Alle Nutzer mit Rolle Admin oder Tester laden
all_users = [u for u in get_all_users() if u["role"] in ("Admin", "Tester")]

# Mapping: user_email → Liste [(testcase, status)]
user_cases = {
    user["email"]: get_testcases_for_week(user["email"], year, week)
    for user in all_users
}

# Immer eine Tabelle anzeigen – auch bei leeren Daten
cols = st.columns(len(all_users))
for i, user in enumerate(all_users):
    u_email = user["email"]
    u_name = user["username"]
    cases = user_cases[u_email]

    all_done_flag = all(status == "erledigt" for _, status in cases) if cases else False
    border = "3px solid gold" if all_done_flag else "1px solid #ccc"

    with cols[i]:
        st.markdown(f"### {u_name}")
        if not cases:
            st.markdown(f"<div style='border:{border}; padding:1em; border-radius:10px;'>–</div>", unsafe_allow_html=True)
        else:
            for tc, status in cases:
                bg = '#fdd' if status == 'offen' else '#dfd'
                st.markdown(f"""
                <div style='background-color:{bg}; border:{border}; padding:1em; border-radius:10px; text-align:center;'>
                    <strong>{tc['title']}</strong><br>
                    <span title='{tc['tooltip']}'>ℹ️</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Status wechseln {tc['id']} ({u_name})") and role != "Beobachter" and u_email == email:
                    data = {
                        "testcase_id": tc['id'],
                        "user_email": email,
                        "year": year,
                        "calendar_week": week,
                        "status": 'erledigt' if status == 'offen' else 'offen'
                    }
                    headers2 = HEADERS.copy(); headers2["Prefer"] = "resolution=merge-duplicates"
                    requests.post(f"{SUPABASE_URL}/rest/v1/testcase_status", headers=headers2, json=data)
                    st.experimental_rerun()

# ---------- Admin: alle Nutzer abrufen ----------
def get_all_users():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/users?select=email,username,role", headers=HEADERS)
    return res.json() if res.status_code == 200 else []

# ---------- Adminbereich ----------
if page == "admin" and token and email:
    user = get_user_profile(email)
    if not user or user.get("role") != "Admin":
        st.error("Zugriff verweigert. Adminrechte erforderlich.")
        st.stop()

    st.sidebar.success(f"✅ Eingeloggt als {email}")
    if st.sidebar.button("Logout"):
        st.markdown(f"<meta http-equiv='refresh' content='0;url=/?page=login'>", unsafe_allow_html=True)
        st.stop()

    st.title("🔧 Adminbereich")

    if not subpage:
        st.subheader("Wähle eine Aktion")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style='border:1px solid #ccc; border-radius:8px; padding:1em; text-align:center;'>
                📋<br><strong>Alle Testcases anzeigen</strong><br>
                <a href='/?page=admin&token={token}&email={urllib.parse.quote(email)}&sub=show'>Öffnen</a>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style='border:1px solid #ccc; border-radius:8px; padding:1em; text-align:center;'>
                ➕<br><strong>Neuen Testcase anlegen</strong><br>
                <a href='/?page=admin&token={token}&email={urllib.parse.quote(email)}&sub=create'>Öffnen</a>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style='border:1px solid #ccc; border-radius:8px; padding:1em; text-align:center;'>
                📅<br><strong>Wochenvorschau</strong><br>
                <a href='/?page=admin&token={token}&email={urllib.parse.quote(email)}&sub=weeks'>Öffnen</a>
            </div>
            """, unsafe_allow_html=True)

    elif subpage == "show":
        st.subheader("📋 Alle Testcases anzeigen")
        res = requests.get(f"{SUPABASE_URL}/rest/v1/testcases", headers=HEADERS)
        if res.status_code == 200:
            st.dataframe(res.json())
        else:
            st.error("Fehler beim Laden.")

    elif subpage == "create":
        st.subheader("➕ Neuen Testcase anlegen")
        title = st.text_input("Titel")
        tooltip = st.text_area("Tooltip")
        area = st.text_input("Bereich (optional)")
        interval = st.selectbox("Intervall (in Wochen)", list(range(1, 13)))
        userlist = [u for u in get_all_users() if u['role'] in ('Admin', 'Tester')]
        assigned = st.multiselect("Tester zuweisen", options=[u["email"] for u in userlist],
                                  format_func=lambda e: next(u["username"] for u in userlist if u["email"] == e))

        if st.button("Speichern"):
            if not title or not tooltip or not assigned:
                st.warning("Bitte alle Pflichtfelder ausfüllen.")
            else:
                payload = {"title": title, "tooltip": tooltip, "area": area or None, "interval_weeks": interval}
                headers_tc = HEADERS.copy()
                headers_tc["Prefer"] = "return=representation"

                res = requests.post(f"{SUPABASE_URL}/rest/v1/testcases", headers=headers_tc, json=payload)

                if res.status_code == 201:
                    try:
                        tc_id = res.json()[0]["id"]
                        data = [{"testcase_id": tc_id, "user_email": e} for e in assigned]
                        headers2 = HEADERS.copy(); headers2["Prefer"] = "return=minimal"
                        r2 = requests.post(f"{SUPABASE_URL}/rest/v1/testcase_assignments", headers=headers2, json=data)
                        if r2.status_code in (201, 204):
                            # Status-Einträge für aktuelle Woche hinzufügen
                            week, year = get_current_week()
                            status_entries = [
                                {
                                    "testcase_id": tc_id,
                                    "user_email": e,
                                    "year": year,
                                    "calendar_week": week,
                                    "status": "offen"
                                }
                                for e in assigned
                            ]
                    
                            headers3 = HEADERS.copy()
                            headers3["Prefer"] = "return=minimal"
                            r3 = requests.post(f"{SUPABASE_URL}/rest/v1/testcase_status", headers=headers3, json=status_entries)
                    
                            if r3.status_code in (201, 204):
                                st.success("Testcase gespeichert und für diese Woche aktiviert.")
                                st.experimental_rerun()
                            else:
                                st.error("Testcase gespeichert, aber Status nicht initialisiert.")
                        else:
                                st.error("Fehler bei Zuweisung.")
                    except Exception as e:
                        st.error("Testcase wurde erstellt, aber keine ID zurückgegeben.")
                else:
                    st.error("Fehler beim Speichern des Testcases.")
                
# ---------- Admin: Wochenvorschau ----------
if subpage == "weeks":
    st.subheader("📅 Wochenvorschau")

    def get_upcoming_testcases():
        cases = requests.get(f"{SUPABASE_URL}/rest/v1/testcases", headers=HEADERS).json()
        assigns = requests.get(f"{SUPABASE_URL}/rest/v1/testcase_assignments", headers=HEADERS).json()
        statuses = requests.get(f"{SUPABASE_URL}/rest/v1/testcase_status", headers=HEADERS).json()

        preview = []
        for offset in range(1, 5):
            target = datetime.date.today() + datetime.timedelta(weeks=offset)
            kw, yr = target.isocalendar().week, target.isocalendar().year

            for tc in cases:
                for assign in [a for a in assigns if a["testcase_id"] == tc["id"]]:
                    filtered = [s for s in statuses if s["testcase_id"] == tc["id"] and s["user_email"] == assign["user_email"] and s["status"] == "erledigt"]
                    filtered.sort(key=lambda x: (x["year"], x["calendar_week"]), reverse=True)
                    last_y, last_kw = (filtered[0]["year"], filtered[0]["calendar_week"]) if filtered else (None, None)

                    def weeks_since(y1, w1, y2, w2):
                        return (y2 - y1) * 52 + (w2 - w1)

                    if not last_y or weeks_since(last_y, last_kw, yr, kw) >= tc["interval_weeks"]:
                        preview.append({
                            "Kalenderwoche": f"{kw}/{yr}",
                            "Testcase": tc["title"],
                            "User": assign["user_email"]
                        })
        return preview

    table = get_upcoming_testcases()
    if table:
        st.dataframe(table)
    else:
        st.info("Keine fälligen Testcases in den nächsten 4 Wochen.")
