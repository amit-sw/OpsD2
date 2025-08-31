import streamlit as st
from supabase import create_client, Client

def get_supabase_client():
    """Creates and returns a Supabase client."""
    SUPABASE_URL = st.secrets.get("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        print(f"Error connecting to Supabase: {e}")
        return None

def get_calendar_events_from_db(supabase):
    """Gets calendar events from the 'calendar_events' table in Supabase."""
    if not supabase:
        return []
    try:
        response = supabase.table('calendar_events').select('*').execute()
        return response.data
    except Exception as e:
        # If the table doesn't exist, return an empty list
        if "relation \"calendar_events\" does not exist" in str(e):
            return []
        st.error(f"Error getting calendar events from database: {e}")
        print(f"Error getting calendar events from database: {e}")
        return []

def update_calendar_events_in_db(supabase, events):
    """Updates the 'calendar_events' table in Supabase with the given events."""
    if not supabase:
        return
    try:
        # Clear the table first.
        supabase.table('calendar_events').delete().neq('event_id', 'dummy_id_to_delete_all').execute()

        # Insert new events
        if events:
            data_to_insert = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                data_to_insert.append({
                    'event_id': event['id'],
                    'summary': event['summary'],
                    'start_time': start,
                    'end_time': end,
                })
            supabase.table('calendar_events').insert(data_to_insert).execute()
        st.success("Calendar events updated in the database.")
    except Exception as e:
        st.error(f"Error updating calendar events in database: {e}")
        print(f"Error updating calendar events in database: {e}")

@st.cache_data(ttl=600)
def get_user_from_db(_supabase, email):
    """Fetches user details from the 'users' table based on email."""
    supabase=_supabase
    if not supabase:
        return None
    try:
        response = supabase.table('authorized_users').select('*').eq('email', email).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error fetching user from database: {e}")
        print(f"Error fetching user from database: {e}")
        return None