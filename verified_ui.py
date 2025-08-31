import streamlit as st
from supabase_integration import get_supabase_client, get_calendar_events_from_db, update_calendar_events_in_db, get_user_from_db
from google_calendar import get_calendar_service, get_calendar_events
from datetime import datetime

def show_ui_core(user):
    name = user.get("name", "Unknown User")
    email = user.get("email", "Unknown Email")
    picture = user.get("picture", "")
    email_verified = user.get("email_verified", False)

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

    st.title("Google Calendar Sync")

    supabase = get_supabase_client()

    if st.button("Refresh from Google Calendar"):
        st.session_state.refreshed_events = None
        start=datetime.now()
        calendar_service = get_calendar_service()
        if calendar_service:
            refreshed_events = get_calendar_events(calendar_service)
            st.session_state.refreshed_events = refreshed_events
            end = datetime.now()
            duration = end - start
            st.success(f"Fetched {len(refreshed_events)} events from Google Calendar in {duration}.")

    if 'refreshed_events' in st.session_state and st.session_state.refreshed_events is not None:
        st.header("Fresh Events from Google Calendar")
        refreshed_events = st.session_state.refreshed_events
        if refreshed_events:
            st.dataframe(refreshed_events)
        else:
            st.write("No upcoming events found in Google Calendar.")

def show_ui_admin(user):
    st.title("Admin Panel")
    st.write("This is the admin panel. More features coming soon!")
    show_ui_core(user)

def show_ui_guest(user):
    st.title("Guest Access")
    st.write(f"You do not have access. Please reach out to System Administrator with your information\n Email: {user.get("email", "Unknown Email")}.")
    if st.button("Log out"):
        st.logout()
    #show_ui_core(user)

def show_ui_user(user):
    st.title("User Access")
    st.write("Welcome to the user panel. More features coming soon!")
    show_ui_core(user)

def show_ui(user):
    if user and user.get("email_verified", False):
        supabase = get_supabase_client()
        if supabase:
            user_record = get_user_from_db(supabase, user['email'])
            if not user_record:
                role = "guest"
                show_ui_guest(user)
                return
            role= user_record.get("role", "guest")
            if role == "admin":
                show_ui_admin(user)
            elif role == "user":
                show_ui_user(user)
            elif role == "guest":
                show_ui_guest(user)
            else:
                st.error(f"Unknown role: {role}. Please contact the administrator.")
        else:
            st.error("Could not connect to Supabase.")
    else:
        st.warning("Please log in with a verified email to access the app.")