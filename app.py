import streamlit as st
from verified_ui import show_ui

    

def login_screen():
    st.button("Log in with Google", on_click=st.login)

if not st.user.is_logged_in:
    login_screen()
else:
    show_ui(st.user)