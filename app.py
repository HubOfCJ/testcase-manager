import streamlit as st
import streamlit_authenticator as stauth

# ---------- Harte Zugangsdaten ----------
credentials = {
    "usernames": {
        "CJ": {
            "email": "CJ@example.com",
            "name": "CJ",
            "password": "$2b$12$Yz.g9U7JZTy4fIE4R.KBJOhAnEExZjmrMu5Ba0ZhNF4FZQAs5n8MC"
        }
    }
}

# ---------- Authentifizierung ----------
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="testcase_login",
    key="abcdef",
    cookie_expiry_days=1
)

name, auth_status, username = authenticator.login("Login", "main")

st.write("auth_status:", auth_status)
st.write("username:", username)

if auth_status:
    st.sidebar.success(f"Eingeloggt als {username}")
    authenticator.logout("Logout", "sidebar")
    st.success("✅ Login erfolgreich! Du kannst jetzt Testcases oder Nutzerbereiche integrieren.")
elif auth_status is False:
    st.error("❌ Login fehlgeschlagen.")
else:
    st.info("Bitte logge dich ein.")
