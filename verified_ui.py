import streamlit as st
from supabase_integration import get_supabase_client, get_calendar_events_from_db, update_calendar_events_in_db
from google_calendar import get_calendar_service, get_calendar_events

def show_ui(user):
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
    db_events = get_calendar_events_from_db(supabase)

    st.header("Calendar Events from Supabase")
    if db_events:
        for event in db_events:
            st.write(f"- {event['summary']} ({event['start_time']} - {event['end_time']})")
    else:
        st.write("No calendar events found in the database.")

    if st.button("Refresh from Google Calendar"):
        st.session_state.refreshed_events = None
        calendar_service = get_calendar_service()
        if calendar_service:
            refreshed_events = get_calendar_events(calendar_service)
            st.session_state.refreshed_events = refreshed_events

    if 'refreshed_events' in st.session_state and st.session_state.refreshed_events is not None:
        st.header("Fresh Events from Google Calendar")
        refreshed_events = st.session_state.refreshed_events
        if refreshed_events:
            for event in refreshed_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                st.write(f"- {event['summary']} ({start} - {end})")

            if st.button("Confirm and Update Supabase"):
                update_calendar_events_in_db(supabase, refreshed_events)
                st.session_state.refreshed_events = None
                st.rerun()
        else:
            st.write("No upcoming events found in Google Calendar.")