import streamlit as st
import bcrypt

# Gehashter Passwort-Hash für "CJ"
stored_hash = "$2b$12$Yz.g9U7JZTy4fIE4R.KBJOhAnEExZjmrMu5Ba0ZhNF4FZQAs5n8MC"

st.title("🔐 Manuelle Auth-Diagnose")

username_input = st.text_input("Benutzername")
password_input = st.text_input("Passwort", type="password")

if st.button("Prüfen"):
    st.write("Raw password:", list(password_input))
    st.write("Length:", len(password_input))    
    password_ok = (password_input == "CJ")
    st.write("✅ Passwort korrekt?" if password_ok else "❌ Passwort falsch")
