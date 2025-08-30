import streamlit as st
from supabase_integration import get_supabase_client, show_waitlist, show_waitlist_form


def show_ui(user):
    name=user.get("name", "Unknown User")
    email=user.get("email", "Unknown Email")
    picture=user.get("picture", "")
    email_verified=user.get("email_verified", False)
    with st.sidebar:
        st.text(f"Welcome {name}\n {email}")
        if email_verified:
            st.success("Email is verified.")
        else:
            st.warning("Email is not verified.")
        if picture:
            st.image(picture, width=100)
        if st.button("Log out"):
            st.logout()
    supabase = get_supabase_client()
    show_waitlist(supabase)
    show_waitlist_form(supabase, email)