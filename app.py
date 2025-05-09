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

# ---------- Vorschau: Welche Testcases werden fällig ----------
def get_upcoming_testcases():
    all_cases = requests.get(f"{SUPABASE_URL}/rest/v1/testcases", headers=HEADERS).json()
    assignments = requests.get(f"{SUPABASE_URL}/rest/v1/testcase_assignments", headers=HEADERS).json()
    statuses = requests.get(f"{SUPABASE_URL}/rest/v1/testcase_status", headers=HEADERS).json()

    upcoming = []
    for offset in range(1, 5):
        target_date = datetime.date.today() + datetime.timedelta(weeks=offset)
        kw = target_date.isocalendar().week
        year = target_date.isocalendar().year
        for tc in all_cases:
            for assign in assignments:
                if assign['testcase_id'] == tc['id']:
                    # Letztes erledigt-Datum prüfen
                    filtered = [s for s in statuses if s['testcase_id'] == tc['id'] and s['user_email'] == assign['user_email'] and s['status'] == 'erledigt']
                    filtered.sort(key=lambda x: (x['year'], x['calendar_week']), reverse=True)
                    last_year, last_kw = (filtered[0]['year'], filtered[0]['calendar_week']) if filtered else (None, None)

                    def weeks_since(y1, w1, y2, w2):
                        return (y2 - y1) * 52 + (w2 - w1)

                    due = False
                    if not last_year:
                        due = True
                    else:
                        if weeks_since(last_year, last_kw, year, kw) >= tc['interval_weeks']:
                            due = True

                    if due:
                        upcoming.append({
                            "KW": f"{kw}/{year}",
                            "Titel": tc['title'],
                            "User": assign['user_email']
                        })
    return upcoming

# ---------- Seiten: Adminbereich (Wochenvorschau) ----------
if page == "admin" and subpage == "weeks" and token and email:
    user = get_user_profile(email)
    if not user or user.get("role") != "Admin":
        st.error("Zugriff verweigert. Adminrechte erforderlich.")
        st.stop()

    st.sidebar.success(f"✅ Eingeloggt als {email}")
    if st.sidebar.button("Zurück zum Adminmenü"):
        st.markdown(f"<meta http-equiv='refresh' content='0;url=/?page=admin&token={token}&email={urllib.parse.quote(email)}'>", unsafe_allow_html=True)
        st.stop()

    st.title("📅 Wochenvorschau")
    data = get_upcoming_testcases()

    if not data:
        st.info("Keine fälligen Testcases in den nächsten vier Wochen.")
    else:
        st.dataframe(data)

# ---------- Home: Tabelle mit Kacheln je Nutzer ----------
def get_testcases_for_week(email, year, week):
    assigned = requests.get(f"{SUPABASE_URL}/rest/v1/testcase_assignments?user_email=eq.{email}", headers=HEADERS).json()
    all_cases = requests.get(f"{SUPABASE_URL}/rest/v1/testcases", headers=HEADERS).json()
    statuses = requests.get(f"{SUPABASE_URL}/rest/v1/testcase_status?user_email=eq.{email}&year=eq.{year}&calendar_week=eq.{week}", headers=HEADERS).json()

    # Filter cases for this week based on interval
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
                status_now = [s for s in statuses if s['testcase_id'] == tc['id']]
                stat = status_now[0]['status'] if status_now else 'offen'
                relevant.append((tc, stat))
    return relevant

# In HOME-Bereich einsetzen:
elif page == "home" and token and email:
    user = get_user_profile(email)
    if not user:
        st.error("Benutzerprofil nicht gefunden.")
        st.stop()

    username = user.get("username")
    role = user.get("role")
    week, year = get_current_week()

    st.sidebar.success(f"✅ Eingeloggt als {email}")
    logout_url = "/?page=login"
    if st.sidebar.button("Logout"):
        st.markdown(f"<meta http-equiv='refresh' content='0;url={logout_url}'>", unsafe_allow_html=True)
        st.stop()

    st.title(f"Willkommen, {username}!")
    st.subheader(f"📆 Kalenderwoche {week}")

    if role == "Admin":
        admin_link = f"/?page=admin&token={token}&email={urllib.parse.quote(email)}"
        st.markdown(f"[🔧 Zum Adminbereich]({admin_link})", unsafe_allow_html=True)

    testcases = get_testcases_for_week(email, year, week)
    if not testcases:
        st.info("Keine Testcases für diese Woche zugewiesen oder fällig.")
    else:
        cols = st.columns(len(testcases))
        for i, (tc, status) in enumerate(testcases):
            bg = '#fdd' if status == 'offen' else '#dfd'
            with cols[i]:
                with st.container():
                    st.markdown(f"""
                        <div style='background-color:{bg}; padding:1em; border-radius:10px; text-align:center;'>
                            <strong>{tc['title']}</strong><br>
                            <span title='{tc['tooltip']}'>ℹ️</span><br><br>
                            <form action="" method="post">
                                <button type="submit">Status wechseln</button>
                            </form>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Status wechseln {tc['id']}") and role != "Beobachter":
                        url = f"{SUPABASE_URL}/rest/v1/testcase_status"
                        data = {
                            "testcase_id": tc['id'],
                            "user_email": email,
                            "year": year,
                            "calendar_week": week,
                            "status": 'erledigt' if status == 'offen' else 'offen'
                        }
                        headers = HEADERS.copy(); headers["Prefer"] = "resolution=merge-duplicates"
                        requests.post(url, headers=headers, json=data)
                        st.experimental_rerun()

# ---------- Funktion: Alle Testcases erledigt? ----------
def all_done(testcases):
    return all(status == 'erledigt' for _, status in testcases)

# ---------- Kachel-Anzeige mit Goldrahmen ----------
    if not testcases:
        st.info("Keine Testcases für diese Woche zugewiesen oder fällig.")
    else:
        border_style = "3px solid gold" if all_done(testcases) else "1px solid #ccc"
        cols = st.columns(len(testcases))
        for i, (tc, status) in enumerate(testcases):
            bg = '#fdd' if status == 'offen' else '#dfd'
            with cols[i]:
                with st.container():
                    st.markdown(f"""
                        <div style='background-color:{bg}; padding:1em; border-radius:10px; border:{border_style}; text-align:center;'>
                            <strong>{tc['title']}</strong><br>
                            <span title='{tc['tooltip']}'>ℹ️</span><br><br>
                            <form action="" method="post">
                                <button type="submit">Status wechseln</button>
                            </form>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Status wechseln {tc['id']}") and role != "Beobachter":
                        url = f"{SUPABASE_URL}/rest/v1/testcase_status"
                        data = {
                            "testcase_id": tc['id'],
                            "user_email": email,
                            "year": year,
                            "calendar_week": week,
                            "status": 'erledigt' if status == 'offen' else 'offen'
                        }
                        headers = HEADERS.copy(); headers["Prefer"] = "resolution=merge-duplicates"
                        requests.post(url, headers=headers, json=data)
                        st.experimental_rerun()
