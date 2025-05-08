import streamlit as st
import streamlit_authenticator as stauth

# ---------- Test-User (hart codiert) ----------
credentials = {
    "usernames": {
        "CJ": {
            "email": "CJ@example.com",
            "name": "CJ",
            "password": "$2b$12$7rDF9Df8kR.fKcfGHwPVMeiy75PRo6iYViIee1upQa3G7XpG/k1wC"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="testcase_login",
    key="abcdef",
    cookie_expiry_days=1
)

login_result = authenticator.login(location="main")
auth_status = login_result.get("authenticated") if login_result else None
username = login_result.get("username") if login_result else None

st.write("auth_status:", auth_status)
st.write("username:", username)

if auth_status:
    st.success(f"Eingeloggt als {username}")
    st.write("🎉 Login erfolgreich – du kannst jetzt die App aufbauen.")
elif auth_status is False:
    st.error("Login fehlgeschlagen.")
else:
    st.info("Bitte logge dich ein.")
